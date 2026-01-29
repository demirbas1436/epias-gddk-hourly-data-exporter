import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
import datetime
import pandas as pd

# Yapılandırma
USERNAME = "USERNAME"
PASSWORD = "PASSWORD"

CAS_BASE_URL = "https://cas.epias.com.tr/cas/v1"
BASE_URL = "https://epys.epias.com.tr/pre-reconciliation"
HOURLY_LIST_URL = f"{BASE_URL}/v1/meter-data/approved-meter-data/hourly/list"

def create_retry_session():
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["POST", "GET"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

def get_tgt(session):
    url = f"{CAS_BASE_URL}/tickets"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "text/plain"
    }
    data = {"username": USERNAME, "password": PASSWORD}
    
    print(f"\n[ADIM 1] TGT alınıyor: {url}...")
    response = session.post(url, headers=headers, data=data, allow_redirects=False)
    
    if response.status_code not in [200, 201]:
        print(f"BAŞARISIZ: Durum {response.status_code}")
        print(response.text)
        response.raise_for_status()

    tgt_location = response.headers.get("Location")
    if tgt_location:
        tgt = tgt_location.split("/")[-1].strip()
    else:
        tgt = response.text.strip()
    
    print(f"BAŞARILI: TGT = {tgt[:15]}...")
    return tgt

def get_st(session, tgt, service_url):
    url = f"{CAS_BASE_URL}/tickets/{tgt}"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"service": service_url}
    
    print(f"[ADIM 2] Servis için ST alınıyor: {service_url}...")
    response = session.post(url, headers=headers, data=data)
    response.raise_for_status()
    
    st = response.text.strip()
    print(f"BAŞARILI: ST = {st[:15]}...")
    return st

def list_hourly_meter_datas(session, tgt, st, page_number=1):
    print(f"\n[ADIM 3] Saatlik Sayaç Verisi Liste Servisi Çağrılıyor (Sayfa {page_number})...")
    url = f"{HOURLY_LIST_URL}?ticket={st}"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "TGT": tgt
    }
    
    # swagger.json'daki HourlyMeterDataReqDto ile eşleşen payload
    payload = {
        "effectiveDateStart": "2025-11-01T00:00:00+03:00",
        "effectiveDateEnd": "2025-11-30T23:59:00+03:00",
        "version": "2025-12-01T00:00:00+03:00",
        "isRetrospective": True,
        "isLastVersion": True,
        "page": {
            "number": page_number,
            "size": 100 # Verimlilik için boyut artırıldı
        }
    }
    
    response = session.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"BAŞARISIZ: Durum {response.status_code}")
        # Mümkünse tam hatayı yazdır
        try:
            error_data = response.json()
            if 'errors' in error_data and error_data['errors']:
                for err in error_data['errors']:
                    print(f"HATA: {err.get('errorCode')} - {err.get('errorMessage')}")
                    if "uyumsuzdur" in err.get('errorMessage', ''):
                        print("İPUCU: Kontrol edilen versiyon tarihi bu dönem için geçerli GDDK yayın tarihiyle eşleşmiyor olabilir.")
        except:
            print(response.text)
        return None

def export_to_excel(all_items):
    if not all_items:
        print("Dışa aktarılacak öğe yok.")
        return

    print(f"\n[ADIM 4] {len(all_items)} kayıt Excel'e aktarılıyor...")
    
    # Excel sütunları için iç içe geçmiş bileşenleri düzleştirme
    flattened_data = []
    for item in all_items:
        row = item.copy()
        
        # Varsa settlementPoint (Uzlaştırma Noktası) bilgisini düzleştir
        sp = row.pop('settlementPoint', {})
        if sp:
            row['settlementPointId'] = sp.get('value')
            row['settlementPointName'] = sp.get('label')
            
        # Varsa meter (Sayaç) bilgisini düzleştir
        meter = row.pop('meter', {})
        if meter:
            row['meterId'] = meter.get('id')
            row['meterName'] = meter.get('name')
            row['meterEic'] = meter.get('eic')
            
        # readingType (Okuma Tipi) bilgisini düzleştir
        rt = row.pop('readingType', {})
        if rt:
            row['readingType'] = rt.get('label')

        # usageType (Kullanım Tipi) bilgisini düzleştir
        ut = row.pop('usageType', {})
        if ut:
            row['usageType'] = ut.get('label')
            
        # meterReadingCompany (Sayaç Okuma Şirketi) bilgisini düzleştir
        mrc = row.pop('meterReadingCompany', {})
        if mrc:
            row['meterReadingCompany'] = mrc.get('label')

        flattened_data.append(row)

    df = pd.DataFrame(flattened_data)
    
    # Excel'e Kaydet
    filename = "hourly_meter_data.xlsx"
    df.to_excel(filename, index=False)
    print(f"BAŞARILI: Veriler {filename} dosyasına aktarıldı")

def main():
    try:
        session = create_retry_session()
        tgt = get_tgt(session)
        
        all_items = []
        current_page = 1
        total_pages = 1
        
        while current_page <= total_pages:
            st = get_st(session, tgt, HOURLY_LIST_URL)
            response_data = list_hourly_meter_datas(session, tgt, st, current_page)
            
            if response_data and 'body' in response_data and response_data['body']:
                content = response_data['body'].get('content', {})
                items = content.get('items', [])
                all_items.extend(items)
                
                # Sayfalama bilgisini kontrol et
                page_info = content.get('page', {})
                print(f"Sayfa verisi alındı: {page_info}")
                
                # Güçlü sayfalama algılama
                api_total_pages = page_info.get('totalPages', page_info.get('totalPageCount'))
                if api_total_pages is not None:
                    total_pages = api_total_pages
                else:
                    # totalPages eksikse, 'total' öğe veya sayfa sayısı olabilir
                    total_val = page_info.get('total', 1)
                    size_val = page_info.get('size', 100)
                    
                    # Sezgisel: total büyükse muhtemelen öğelerdir, küçükse muhtemelen sayfalardır
                    # Ancak güvenli olmakta fayda var: EPYS'de Sayfa içindeki 'total' genellikle toplam öğe sayısıdır
                    if total_val > 50: # Arbitrary threshold, but usually more than total pages
                        total_pages = (total_val + size_val - 1) // size_val
                    else:
                        total_pages = total_val
                
                print(f"Sayfa {current_page}/{total_pages} getirildi ({len(items)} öğe, Toplam: {len(all_items)})")
                
                current_page += 1
            else:
                if response_data:
                    print(f"Sayfa {current_page} konumunda durduruluyor - Gövde boş veya hata oluştu.")
                else:
                    print(f"Sayfa {current_page} konumunda durduruluyor - Yanıt verisi yok.")
                break
        
        if all_items:
            export_to_excel(all_items)
        else:
            print("İşlenecek veri bulunamadı.")

    except Exception as e:
        print(f"\nBir hata oluştu: {e}")

if __name__ == "__main__":
    main()
