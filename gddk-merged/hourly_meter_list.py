import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
import datetime
import pandas as pd
import os

# Betiğin bulunduğu dizini tespit et
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Yapılandırma
USERNAME = "USERNAME"
PASSWORD = "PASSWORD"

effective_start_str = "2025-10-01T00:00:00+03:00"
effective_end_str = "2025-10-31T23:59:00+03:00"

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

def list_hourly_meter_datas(session, tgt, st, page_number, version_date_str, effective_start, effective_end):
    print(f"\n[ADIM 3] Saatlik Sayaç Verisi Liste Servisi Çağrılıyor (Sayfa {page_number})...")
    url = f"{HOURLY_LIST_URL}?ticket={st}"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "TGT": tgt
    }
    
    # swagger.json'daki HourlyMeterDataReqDto ile eşleşen payload
    payload = {
        "effectiveDateStart": effective_start,
        "effectiveDateEnd": effective_end,
        "version": version_date_str,
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

def fetch_data_for_version(session, tgt, version_date_str, effective_start, effective_end):
    """Belirli bir versiyon için tüm sayfalı verileri çeker"""
    all_items = []
    current_page = 1
    total_pages = 1
    
    while current_page <= total_pages:
        st = get_st(session, tgt, HOURLY_LIST_URL)
        response_data = list_hourly_meter_datas(
            session, tgt, st, current_page, version_date_str, effective_start, effective_end
        )
        
        if response_data and 'body' in response_data and response_data['body']:
            content = response_data['body'].get('content', {})
            items = content.get('items', [])
            all_items.extend(items)
            
            # Sayfalama bilgisini kontrol et
            page_info = content.get('page', {})
            
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
            
            print(f"  Sayfa {current_page}/{total_pages} getirildi ({len(items)} öğe, Toplam: {len(all_items)})")
            
            current_page += 1
        else:
            if response_data:
                print(f"  Sayfa {current_page} konumunda durduruluyor - Gövde boş veya hata oluştu.")
            else:
                print(f"  Sayfa {current_page} konumunda durduruluyor - Yanıt verisi yok.")
            break
    
    return all_items

def export_to_excel(all_items, filename, version_label):
    if not all_items:
        print("Dışa aktarılacak öğe yok.")
        return

    print(f"  {len(all_items)} kayıt Excel'e aktarılıyor...")
    
    # Excel sütunları için iç içe geçmiş bileşenleri düzleştirme
    flattened_data = []
    for item in all_items:
        row = item.copy()
        row['versiyon_bilgisi'] = version_label
        
        # Tüm sözlük yapılarını otomatik olarak düzleştir (Veri kaybını önlemek için)
        keys_to_flatten = ['settlementPoint', 'meter', 'readingType', 'usageType', 'meterReadingCompany']
        for key in keys_to_flatten:
            if key in row and isinstance(row[key], dict):
                obj = row.pop(key)
                for sub_key, value in obj.items():
                    # Yeni sütun adı: nesne_özellik (örneğin: meter_id, meter_name)
                    row[f"{key}_{sub_key}"] = value

        flattened_data.append(row)

    df = pd.DataFrame(flattened_data)
    
    # Excel'e Kaydet (Mutlak yol kullan)
    path = os.path.join(SCRIPT_DIR, filename)
    df.to_excel(path, index=False)
    print(f"  BAŞARILI: Veriler {filename} dosyasına aktarıldı\n")

def merge_excel_files(filenames, output_filename):
    """Oluşturulan Excel dosyalarını birleştirir, en yeni versiyonu önceliklendirir"""
    print(f"\n{'*'*60}")
    print(f"[BİRLEŞTİRME] {len(filenames)} dosya birleştiriliyor...")
    print(f"{'*'*60}")
    
    all_dfs = []
    for f in filenames:
        try:
            # Okurken mutlak yol oluştur
            path = os.path.join(SCRIPT_DIR, f)
            df = pd.read_excel(path)
            print(f"    {f}: {len(df)} satır yüklendi")
            all_dfs.append(df)
        except Exception as e:
            print(f"  HATA: {f} okunurken hata oluştu: {e}")
    
    if not all_dfs:
        print("  Birleştirilecek veri bulunamadı.")
        return
        
    # Tüm verileri birleştir
    merged_df = pd.concat(all_dfs, ignore_index=True)
    
    # Sıralama: Versiyon sütununa göre büyükten küçüğe (en yeni versiyon en üstte)
    if 'versiyon_bilgisi' in merged_df.columns:
        merged_df = merged_df.sort_values(by='versiyon_bilgisi', ascending=False)
    
    # Benzersiz anahtara göre tekrarları kaldır (en yeniyi tut)
    # Saatlik veri olduğu için 'effectiveDate' (tarih+saat içerir) bilgisini kullanıyoruz
    # Hem orijinal (meterId) hem de düzleştirilmiş (meter_id) sütun isimlerini kontrol ediyoruz
    subset_cols = ['meterId', 'meter_id', 'effectiveDate']
    available_cols = [c for c in subset_cols if c in merged_df.columns]
    
    if available_cols:
        before_count = len(merged_df)
        merged_df = merged_df.drop_duplicates(subset=available_cols, keep='first')
        after_count = len(merged_df)
        print(f"  Tekrarlar temizlendi (En yeni versiyonlar korundu): {before_count} -> {after_count}")
    
    # Sıralama: Son olarak kullanıcı kolaylığı için sayaç ve tarihe göre artan sıralama
    # meterId veya meter_id hangisi varsa ona göre sırala
    sort_cols = ['meterId', 'meter_id', 'effectiveDate']
    final_sort_cols = [c for c in sort_cols if c in merged_df.columns]
    if final_sort_cols:
        merged_df = merged_df.sort_values(by=final_sort_cols, ascending=True)
        print(f"  Veriler sıralandı: {final_sort_cols}")
    
    # Birleşen sayaç listesini yazdır ve versiyon özeti çıkar
    meter_col = 'meterId' if 'meterId' in merged_df.columns else 'meter_id' if 'meter_id' in merged_df.columns else None
    if meter_col and 'versiyon_bilgisi' in merged_df.columns:
        print(f"  [SÜRÜM ÖZETİ] Sayaç bazlı versiyon takibi:")
        unique_meters = merged_df[meter_col].unique().tolist()
        for meter in unique_meters:
            meter_data = merged_df[merged_df[meter_col] == meter]
            versions = sorted(meter_data['versiyon_bilgisi'].unique().tolist())
            latest = versions[-1] # Sıralı listenin sonuncusu en yenidir
            
            # Eğer birden fazla versiyon varsa çakışma detayını yazdır
            if len(versions) > 1:
                print(f"    - Sayaç {meter}: {versions} versiyonları bulundu. Çakışan kayıtlarda {latest} (en yeni) tercih edildi.")
            else:
                print(f"    - Sayaç {meter}: Sadece {latest} versiyonunda veri bulundu.")
    
    # Mutlak yol ile kaydet
    final_path = os.path.join(SCRIPT_DIR, output_filename)
    merged_df.to_excel(final_path, index=False)
    print(f"  TAMAMLANDI: Birleştirilmiş veri {output_filename} dosyasına kaydedildi.\n")

def generate_month_range(start_date, end_date):
    """İki tarih arasındaki ayları geri döndürür (en yeniden en eskiye)"""
    months = []
    current = start_date
    
    while current >= end_date:
        months.append(current)
        # Bir önceki aya git
        if current.month == 1:
            current = current.replace(year=current.year - 1, month=12)
        else:
            current = current.replace(month=current.month - 1)
    
    return months

def main():
    try:
        # Tarih aralığını hesapla
        # Efektif başlangıç tarihini ayrıştır (Global değişkenleri kullanıyoruz)
        effective_start_dt = datetime.datetime.fromisoformat(effective_start_str.replace('+03:00', ''))
        
        # Geçerli sistem tarihini al
        current_dt = datetime.datetime.now()
        current_month_start = current_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Bitiş versiyonu = Efektif ay + 1 ay
        if effective_start_dt.month == 12:
            end_version_dt = effective_start_dt.replace(year=effective_start_dt.year + 1, month=1)
        else:
            end_version_dt = effective_start_dt.replace(month=effective_start_dt.month + 1)
        
        # Ayları oluştur (geçerli aydan bitiş versiyonuna kadar)
        months = generate_month_range(current_month_start, end_version_dt)
        
        # Görüntüleme için tarihleri formatla
        fmt_start = effective_start_str.split('T')[0]
        fmt_end = effective_end_str.split('T')[0]
        
        print(f"\n{'='*60}")
        print(f"ÇOK VERSİYONLU SAATLIK SAYAÇ VERİSİ DIŞA AKTARIMI")
        print(f"{'='*60}")
        print(f"Efektif Tarih Aralığı: {fmt_start} - {fmt_end}")
        print(f"Versiyon Aralığı: {current_month_start.strftime('%Y-%m')} → {end_version_dt.strftime('%Y-%m')}")
        print(f"Toplam İşlenecek Versiyon: {len(months)}")
        print(f"{'='*60}\n")
        
        session = create_retry_session()
        tgt = get_tgt(session)
        
        generated_files = []
        
        # Ana döngü öncesi efektif dönem etiketi (Örn: 2025-09)
        eff_period_label = effective_start_dt.strftime('%Y-%m')
        
        # Her ay için döngü
        for idx, month_dt in enumerate(months, 1):
            version_str = month_dt.strftime('%Y-%m-01T00:00:00+03:00')
            month_label = month_dt.strftime('%Y-%m')
            
            print(f"[VERSİYON {idx}/{len(months)}] İşleniyor: {month_dt.strftime('%Y-%m')}")
            
            # Bu versiyon için verileri çek
            items = fetch_data_for_version(
                session, tgt, version_str, effective_start_str, effective_end_str
            )
            
            # Excel'e aktar
            if items:
                # Yeni açıklayıcı dosya ismi formatı
                filename = f"GDDK_{eff_period_label}_Versiyon_{month_label}.xlsx"
                export_to_excel(items, filename, month_label)
                generated_files.append(filename)
            else:
                print(f"  Bu versiyon için veri bulunamadı.\n")
        
        # Dosyaları birleştir
        if generated_files:
            merged_filename = f"GDDK_{eff_period_label}_BIRLESTIRILMIS.xlsx"
            merge_excel_files(generated_files, merged_filename)
        
        print(f"{'='*60}")
        print(f"TÜM İŞLEMLER BAŞARIYLA TAMAMLANDI!")
        print(f"{'='*60}")

    except Exception as e:
        print(f"\nBir hata oluştu: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()


