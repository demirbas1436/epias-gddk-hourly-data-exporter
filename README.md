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

- 🔐 **Güvenli Kimlik Doğrulama**: EPİAŞ CAS (Central Authentication Service) sistemi ile TGT ve ST biletleme mekanizması.
- 📑 **Akıllı Sayfalama (Pagination)**: Binlerce satırlık veriyi, tüm sayfaları otomatik gezerek eksiksiz indirme.
- 🧹 **Gelişmiş Veri Düzleştirme (Flattening)**: JSON içerisinde gömülü olan `settlementPoint`, `meter`, `readingType` gibi karmaşık nesneleri Excel sütunlarına dönüştürme.
- 📊 **Profesyonel Excel Çıktısı**: Verileri analiz edilebilir, temiz ve düzenli bir `.xlsx` dosyasında sunma.
- 🔄 **Dayanıklı Bağlantı (Retry)**: Bağlantı hatalarına veya sunucu yoğunluğuna karşı otomatik yeniden deneme mekanizması.
- 🇹🇷 **Tam Türkçe Destek**: Terminal çıktıları, hata mesajları ve işlem logları tamamen Türkçe dilinde.

## 🔧 Gereksinimler

### Python Sürümü
- Python 3.8 veya üzeri

### Bağımlılıklar
```bash
pip install requests pandas openpyxl
```

## 📥 Kurulum

1. **Projeyi indirin** veya kaynak kodları yerel diskinize kopyalayın.
2. **Bağımlılıkları yükleyin**:
   ```bash
   pip install requests pandas openpyxl
   ```

## ⚙️ Yapılandırma

`hourly_meter_list.py` dosyası içerisindeki `Yapılandırma` bölümünü kendi bilgilerinizle güncelleyin:

```python
# Yapılandırma
USERNAME = "EPİAŞ_KULLANICI_ADINIZ"
PASSWORD = "EPİAŞ_ŞİFRENİZ"
```

### Tarih ve Versiyon Ayarları
`list_hourly_meter_datas` fonksiyonu içerisinde aşağıdaki parametreleri değiştirebilirsiniz:
- `effectiveDateStart`: Veri başlangıç tarihi (örn: 2025-11-01)
- `effectiveDateEnd`: Veri bitiş tarihi (örn: 2025-11-30)
- `version`: GDDK yayın versiyon tarihi

## 🚀 Kullanım

Uygulamayı çalıştırmak için terminalde şu komutu çalıştırın:

```bash
python hourly_meter_list.py
```

### İşlem Akışı
1. **ADIM 1**: TGT (Ticket Granting Ticket) anahtarı alınır.
2. **ADIM 2**: İlgli servis için ST (Service Ticket) biletleri üretilir.
3. **ADIM 3**: Sayfa sayfa veri çekme işlemi başlar. Her sayfanın geliş durumu loglanır.
4. **ADIM 4**: Tüm veriler bellekte birleştirilir, düzleştirilir ve Excel dosyasına yazılır.

## 📁 Proje Yapısı

```
gddk-türkçe/
│
├── hourly_meter_list.py      # Ana uygulama dosyası (API ve Veri İşleme)
├── README.md                 # Bu dokümantasyon dosyası
└── hourly_meter_data.xlsx    # Oluşturulan Excel çıktısı (Çalıştırma sonrası)
```

## 🔍 Teknik Detaylar

### Veri Düzleştirme (Flattening) Mantığı
API'den gelen veri yapısı iç içe geçmiş nesneler içerir. Uygulama bu nesneleri şu şekilde sütunlara ayırır:

| Kaynak Nesne | Excel Sütun Adı |
|--------------|-----------------|
| `settlementPoint` | `settlementPointId`, `settlementPointName` |
| `meter` | `meterId`, `meterName`, `meterEic` |
| `readingType` | `readingType` (Etiket Değeri) |
| `usageType` | `usageType` (Etiket Değeri) |

### Kullanılan Teknolojiler
- **Bağlantı**: `requests.Session` ve `HTTPAdapter` ile performanslı bağlantı havuzu.
- **Güvenlik**: CAS v1 Protokolü.
- **Veri İşleme**: `Pandas` (Veri setlerini yönetmek ve Excel'e dönüştürmek için).

## 🐛 Sorun Giderme

- **"BAŞARISIZ: Durum 401"**: Kullanıcı adı veya şifrenizi kontrol edin.
- **"İPUCU: Kontrol edilen versiyon tarihi..."**: Girdiğiniz versiyon tarihinin ilgili dönem için yayınlanmış bir GDDK tarihi olduğundan emin olun.
- **"ModuleNotFoundError"**: `pip install requests pandas openpyxl` komutunu çalıştırdığınızdan emin olun.

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
  <sub>Enerji sektörü için açık kaynak çözümler</sub>
</div>
