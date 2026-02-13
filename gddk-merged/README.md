# 📊 EPİAŞ Saatlik Sayaç Veri Aktarıcı (GDDK)

EPİAŞ (Enerji Piyasaları İşletme A.Ş.) EPYS sisteminden Geriye Dönük Düzeltme Kalemi (GDDK) kapsamındaki saatlik sayaç verilerini otomatik olarak çeken, işleyen ve Excel formatına dönüştüren profesyonel bir veri otomasyon aracı.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Pandas](https://img.shields.io/badge/pandas-2.0+-green.svg)
![EPİAŞ API](https://img.shields.io/badge/EPİAŞ-API-orange.svg)

## 📋 İçindekiler

- [Özellikler](#-özellikler)
- [Gereksinimler](#-gereksinimler)
- [Kurulum](#-kurulum)
- [Yapılandırma](#-yapılandırma)
- [Kullanım](#-kullanım)
- [Proje Yapısı](#-proje-yapısı)
- [Teknik Detaylar](#-teknik-detaylar)
- [Sorun Giderme](#-sorun-giderme)
- [İletişim](#-iletişim)

## ✨ Özellikler

- 🔐 **Güvenli Kimlik Doğrulama**: EPİAŞ CAS biletleme mekanizması (TGT/ST).
- 🔄 **Çoklu Versiyon Taraması**: Belirtilen efektif tarih için geçerli aydan geriye doğru tüm yayın versiyonlarını otomatik tarama.
- 🤝 **Akıllı Veri Birleştirme (Merge)**: Farklı versiyonlardaki verileri tek bir dosyada birleştirme ve **en güncel versiyona otomatik öncelik verme**.
- 📑 **Akıllı Sayfalama**: Binlerce satırlık veriyi tüm sayfaları gezerek eksiksiz indirme.
- 🧹 **Tam Veri Düzleştirme (Flattening)**: JSON içindeki tüm alt nesneleri (`meter`, `settlementPoint` vb.) veri kaybı olmadan Excel sütunlarına dönüştürme.
- 📉 **Otomatik Sıralama**: Çıktı dosyasını sayaç ve tarih bazlı (`meterId` + `effectiveDate`) kronolojik olarak sıralama.
- 🇹🇷 **Tam Türkçe Destek**: Terminal çıktıları ve loglar tamamen Türkçe.

## 🔧 Gereksinimler

- Python 3.8 veya üzeri
- Bağımlılıklar:
  ```bash
  pip install requests pandas openpyxl
  ```

## 📥 Kurulum

1. Proje dosyalarını yerel diskinize kopyalayın.
2. Bağımlılıkları yükleyin: `pip install requests pandas openpyxl`

## ⚙️ Yapılandırma

`hourly_meter_list.py` dosyasının en üstündeki değişkenleri güncelleyin:

```python
# Kullanıcı Bilgileri
USERNAME = "KULLANICI_ADINIZ"
PASSWORD = "SIFRENIZ"

# Hedef Dönem Ayarları
effective_start_str = "2025-10-01T00:00:00+03:00"
effective_end_str = "2025-10-31T23:59:00+03:00"
```

## 🚀 Kullanım

Terminalde çalıştırın:
```bash
python hourly_meter_list.py
```

### İşlem Akışı
1. **Dönem Analizi**: Hedef aydan bugüne kadar olan tüm olası GDDK versiyonları hesaplanır.
2. **Veri Çekme**: Her versiyon için tek tek API sorgusu yapılır ve açıklayıcı isimli Excel dosyaları oluşturulur (Örn: `GDDK_2025-11_Versiyon_2026-02.xlsx`).
3. **Birleştirme (Merge)**: Tüm dosyalar okunur, aynı gün/saat verisi için en yeni tarihli versiyon seçilir. Sayaç bazlı versiyon seçimi loglarda detaylı olarak raporlanır.
4. **Sıralama ve Kayıt**: Veriler kronolojik sıraya sokulur ve `GDDK_2025-11_BIRLESTIRILMIS.xlsx` olarak kaydedilir.

## 📁 Proje Yapısı

```
gddk-türkçe/
│
├── hourly_meter_list.py              # Ana uygulama dosyası (API ve Veri İşleme)
├── README.md                         # Bu dokümantasyon dosyası
├── GDDK_2025-11_Versiyon_2025-12.xlsx # Bireysel versiyon çıktısı
└── GDDK_2025-11_BIRLESTIRILMIS.xlsx  # Final birleştirilmiş ve sıralanmış çıktı
```

## 🔍 Teknik Detaylar

### Birleştirme ve Loglama Mantığı
- **Önceliklendirme**: Eğer bir sayaç için birden fazla versiyonda veri varsa, sistem otomatik olarak en güncel versiyonu (yukarıdaki örnekte 2026-02) tercih eder.
- **Şeffaf Raporlama**: Birleştirme sonunda her bir sayaç için hangi versiyonların bulunduğu ve hangisinin "en yeni" olarak seçildiği terminalde özetlenir.
- **Sıralama**: Final dosyası `meterId` ve `effectiveDate` (tarih+saat) bazında artan sırada sıralanır.

### Veri Yapısı
Düzleştirilen sütunlar `nesne_özellik` formatındadır:
- `meter_id`, `meter_name`, `meter_eic`
- `settlementPoint_value`, `settlementPoint_label`
- `readingType_label`, `usageType_label`

### Kullanılan Teknolojiler
- **Bağlantı**: `requests.Session` ve `HTTPAdapter` ile performanslı bağlantı havuzu.
- **Güvenlik**: CAS v1 Protokolü.
- **Veri İşleme**: `Pandas` (Veri setlerini yönetmek ve Excel'e dönüştürmek için).

## 🐛 Sorun Giderme

- **Veri Eksik Görünüyor**: Excel'in en sağındaki `versiyon_bilgisi` sütununu kontrol ederek verinin hangi versiyondan geldiğini teyit edin.
- **Bağlantı Hatası**: İnternet bağlantınızı ve EPİAŞ servislerinin durumunu kontrol edin. Betik hatalarda 5 kez otomatik yeniden deneme yapar.

## 📧 İletişim

**Murat Demirbaş**

- 📧 E-posta: [demirbas1436@gmail.com](mailto:demirbas1436@gmail.com)
- 📱 Telefon: 05365689025
- 💼 LinkedIn: [linkedin.com/in/muratdemirbas1436](https://tr.linkedin.com/in/muratdemirbas1436)
- ⭐ GitHub: [github.com/demirbas1436](https://github.com/demirbas1436)

---

## 🙏 Teşekkürler

Bu uygulamayı kullandığınız için teşekkür ederiz! Herhangi bir sorun, öneri veya geri bildiriminiz için lütfen bizimle iletişime geçin.

**Faydalı olması dileğiyle!** 💙

---

<div align="center">
  Made with ❤️ by Murat Demirbaş
  <br>
  <sub>Enerji sektörü için profesyonel veri çözümleri</sub>
</div>
