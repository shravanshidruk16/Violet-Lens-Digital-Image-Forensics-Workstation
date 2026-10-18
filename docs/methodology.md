# Digital Image Forensics Methodology & Scientific Principles

## 1. Overview
Violet Lens operates on established principles of digital forensics, signal processing, and computational imaging. This document delineates the mathematical, structural, and empirical foundations of each forensic module implemented in the workstation, alongside its investigative capabilities and technical boundaries.

---

## 2. Cryptographic Integrity Hashing (SHA-256)

### Mathematical Formulation
A cryptographic hash function $H: \{0,1\}^* \rightarrow \{0,1\}^{256}$ maps an arbitrary byte sequence $M$ to a deterministic 256-bit digest $h = H(M)$. Violet Lens computes this digest using the FIPS 180-4 standard SHA-256 algorithm.

$$\text{SHA-256}(M) = \text{Digest}_{256}$$

### Evidentiary Role
In digital forensics, establishing chain of custody requires cryptographic assurance that evidence has not undergone alteration from the time of acquisition or ingestion. By hashing the raw binary stream immediately upon receipt:
1. Bit-level identity is established.
2. Any modification of a single bit yields an entirely different hash due to the avalanche effect.
3. Third-party analysts can independently recompute the hash to verify bit-level consistency.

### Methodological Limitation
A cryptographic hash verifies only that the byte sequence has not changed since hash generation. It does **not** prove:
- That the image is genuine or unedited prior to hash generation.
- The real-world scene actually occurred.
- The identity of the camera owner.

---

## 3. File Signature & Container Consistency

### Principles
Modern operating systems often rely on file extensions (`.jpg`, `.png`, `.webp`) to determine file association. However, extensions can be trivially renamed or obfuscated. Digital forensics verifies format integrity by reading the initial binary headers ("magic bytes"):

| Format | Magic Bytes (Hexadecimal) | Standard Offset |
|---|---|---|
| **JPEG** | `FF D8 FF` | Byte 0 |
| **PNG** | `89 50 4E 47 0D 0A 1A 0A` | Byte 0 |
| **WebP** | `52 49 46 46 ... 57 45 42 50` (`RIFF....WEBP`) | Bytes 0-3, 8-11 |
| **TIFF (Little Endian)** | `49 49 2A 00` (`II*\x00`) | Byte 0 |
| **TIFF (Big Endian)** | `4D 4D 00 2A` (`MM\x00*`) | Byte 0 |
| **BMP** | `42 4D` (`BM`) | Byte 0 |

### Evaluative Boundary
A signature-to-extension mismatch is an investigative flag. While it can occur legitimately through innocent user renaming or export bugs, in an evidentiary context it demands scrutiny to ensure payload obfuscation or tool mismatch is not present.

---

## 4. EXIF & Structural Metadata

### Principles
Exchangeable Image File Format (EXIF) standardizes metadata storage within JPEG, TIFF, and WebP containers. The metadata segment stores:
- **Camera Device Parameters**: Make, Model, Lens Specification, Serial Number.
- **Software Processing Tags**: Editing suites such as Adobe Photoshop, GIMP, or mobile camera apps.
- **Timestamps**:
  - `DateTimeOriginal`: Exposure moment recorded by hardware clock.
  - `DateTimeDigitized`: Sensor digitization moment.
  - `DateTime`: File modification or re-save timestamp.
- **Exposure Optics**: Aperture ($f$-stop), Exposure Time ($1/t$ s), ISO speed ratings, Focal Length, Flash status.
- **Geolocation (GPS)**: Latitude, Longitude, Altitude, and GPS atomic clock timestamps.

### Privacy-Preserving Architecture
Geolocation data is treated as sensitive Personal Identifiable Information (PII). Violet Lens flags GPS presence while privacy-masking exact coordinates by default. Analysts can unmask coordinates locally on demand.

### Evidentiary Boundary
- Metadata resides in user-modifiable headers and can be injected, forged, or wiped with command-line tools (e.g. ExifTool).
- Social media platforms (e.g., WhatsApp, Instagram, Facebook, X) strip EXIF metadata during upload to conserve bandwidth and protect user privacy. Thus, **absence of EXIF does not indicate forgery**.
- Conversely, valid camera EXIF does not guarantee that pixel layers have not been modified.

---

## 5. Error Level Analysis (ELA)

### Signal Processing Foundation
JPEG uses lossy compression based on $8 \times 8$ Discrete Cosine Transform (DCT) pixel blocks. Each $8 \times 8$ block of color frequencies is quantized against a quality matrix:

$$F_{Q}(u, v) = \text{round}\left(\frac{\text{DCT}(u, v)}{Q(u, v)}\right)$$

When an image is saved repeatedly under lossy compression, the rate of quantization error decreases until reaching an equilibrium for that specific quality level.

### Algorithm
1. The image $I_{\text{orig}}$ is loaded and converted to RGB color space.
2. An in-memory recompression pass saves the image as JPEG at a documented quality ($Q = 90$):
   $$I_{\text{recomp}} = \text{JPEG}_{Q=90}(I_{\text{orig}})$$
3. The absolute difference matrix is calculated per pixel across all color planes:
   $$\Delta(x, y, c) = |I_{\text{orig}}(x, y, c) - I_{\text{recomp}}(x, y, c)|$$
4. An amplification scale factor $S = 15$ is applied for human visual review:
   $$E_{\text{ELA}}(x, y, c) = \min(255, \Delta(x, y, c) \times S)$$
5. Radiometric error metrics are computed:
   - $\mu_{\text{error}} = \frac{1}{N}\sum \Delta$
   - $\sigma_{\text{error}} = \sqrt{\frac{1}{N}\sum (\Delta - \mu)^2}$
   - $\text{High Error Ratio} = \frac{|\{(x,y) : \Delta(x,y) > 10\}|}{N} \times 100\%$

### Interpretation & Scientific Boundaries
- **Uniform Compression History**: Regions sharing an identical compression history typically exhibit consistent error distributions.
- **Splicing & Resaving**: Pasting an uncompressed text element or an object from another image into an existing JPEG often creates localized error discontinuities because the spliced region has undergone fewer compression cycles.
- **High-Frequency Content Warning**: Sharp visual boundaries, textured foliage, and high-contrast edges inherently generate higher DCT high-frequency error. **Bright regions in ELA do not automatically equal manipulation.**
- **Non-JPEG Restriction**: ELA is designed for JPEG DCT grids. Violet Lens strictly disables standard ELA on lossless PNG, WebP, or BMP files to avoid generating misleading forensic artifacts.

---

## 6. Radiometric Pixel Histograms & Shannon Entropy

### Channel Distributions
Violet Lens computes 256-bin histograms across Red, Green, Blue, and Luminance channels (ITU-R BT.601 standard):

$$Y = 0.299R + 0.587G + 0.114B$$

### Shannon Information Entropy
Entropy measures the average information density and randomness within the image:

$$H = -\sum_{i=0}^{255} P(i) \log_2 P(i)$$

Where $P(i)$ is the empirical probability of intensity level $i$. In an 8-bit channel, theoretical entropy ranges from $0$ (completely flat solid color) to $8.0$ bits/pixel (maximally distributed information/noise).

### Dynamic Range Clipping
Clipping occurs when pixel values exceed the sensor or storage dynamic range:
- **Shadow Clipping**: $\frac{|\{p : p \le 1\}|}{N} \times 100\%$
- **Highlight Clipping**: $\frac{|\{p : p \ge 254\}|}{N} \times 100\%$

Abnormal spikes or periodic gaps ("comb effect") across the histogram indicate aggressive level stretching or histogram equalization.

---

## 7. Deterministic Observation Taxonomy

Violet Lens avoids speculative "tamper percentages" or probabilistic authenticity claims. Observations are strictly categorized as:

1. **Information (`info`)**: Empirical facts (SHA-256 fingerprint, resolution, camera model, verified magic bytes).
2. **Needs Review (`review`)**: Discrepancies or editing indicators requiring human investigator analysis (software tags like Photoshop, extension mismatches, heavy dynamic range clipping, high ELA variance).
3. **Analysis Limitation (`limitation`)**: Methodological boundaries (e.g. non-JPEG format precludes ELA, missing EXIF is common, hash proves sequence integrity only).
