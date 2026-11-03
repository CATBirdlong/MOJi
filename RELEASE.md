# MOJi Dictionary 9.1.1 - Community Build (Unsigned)

> Release asset: `MOJiDict-9.1.1-final-unsigned-aligned.apk` (zipaligned, unsigned)
> Size: 171,323,622 bytes (163.39 MB)
> SHA-256: `1CF1DB3924756015C6820B9181B1D4D6C4BEA7BE4B0713F0D378A2E2AA2C3000`

---

## 1. Why this build is unsigned

Nobody should trust a binary that someone else signed. This asset ships **before** signing, so you
apply your own key and verify the result yourself. Two consequences:

- The APK will **not install over** an existing MOJi installation (different signing certificate).
- Your key becomes the identity of the app for the lifetime of that installation.

---

## 2. The baseline APK is not distributed here

This release contains only the **patched APK**. The upstream package is commercial software and is
not redistributed by this repository. To rebuild from source you must obtain the original APK
yourself; the patch offsets are byte-based, so the baseline must match exactly.

| Property | Expected value |
| --- | --- |
| Package name | `com.mojitec.mojidict` |
| versionCode / versionName | 1742 / 9.1.1 |
| Size | 168,579,643 bytes |
| SHA-256 | `EA99ECF16DE79C9C4C21ED3F8B670DAF6406657E798C86ED73E288121FD0F22D` |

### Verify the baseline

Windows PowerShell:

```powershell
(Get-Item .\mojidict-9.1.1.apk).Length
Get-FileHash .\mojidict-9.1.1.apk -Algorithm SHA256
```

Linux / macOS:

```bash
stat -c %s mojidict-9.1.1.apk
sha256sum mojidict-9.1.1.apk
```

If either value differs, stop: the build scripts will patch the wrong bytes.

---

## 3. Sign the APK with your own key

### 3.1 Create a keystore (once)

```bash
keytool -genkeypair -v -keystore my-release.jks -alias moji \
  -keyalg RSA -keysize 2048 -validity 10000
```

### 3.2 Sign (APK Signature Scheme v2 + v3)

```bash
apksigner sign \
  --ks my-release.jks --ks-key-alias moji \
  --min-sdk-version 26 \
  --out MOJiDict-9.1.1-signed-by-me.apk \
  MOJiDict-9.1.1-final-unsigned-aligned.apk
```

### 3.3 Verify

```bash
apksigner verify --print-certs MOJiDict-9.1.1-signed-by-me.apk
```

Expected: `Verified using v2 scheme` / `v3 scheme`, and your DN under `Signer #1 certificate DN`.

### 3.4 Install

```bash
adb install -r MOJiDict-9.1.1-signed-by-me.apk
```

If a previous MOJi build is installed, uninstall it first (`adb uninstall com.mojitec.mojidict`).
Uninstalling **erases app data** - back it up beforehand if you need it.

---

## 4. What this build changes

Thirteen byte-level patches over three files, all equal-length rewrites, so no structural
DEX/resource rebuild is involved:

| Area | Effect |
| --- | --- |
| Membership state | Account reads as activated; `isPro` true; expiry 2099-01-01; lifetime flag kept true |
| Entry detail | The "view all definitions and examples" paywall no longer covers the content |
| Teaching examples | The same gate on teaching sentences is lifted |
| Desktop widget | Renders the content branch instead of the permission hint |
| AI mnemonic | The module becomes visible (content still requires a server response) |
| Wallet display | MO coin / MO point values render as 9999 (cosmetic only) |
| AI points label | Renders an infinity glyph instead of the number (cosmetic only) |

---

## 5. What it does not change

- **Favorite-count limits, memorization quotas, entry-detail data and AI content are enforced
  server-side.** No client patch can raise them; the app will still refuse the 11th favorite.
- Numbers are cosmetic: consuming features still check the real server-side balance.
- Nothing is proxied or intercepted; there is no MITM component and no network redirection.

---

## 6. Verify this asset before installing

```bash
sha256sum MOJiDict-9.1.1-final-unsigned-aligned.apk
# expected: 1CF1DB3924756015C6820B9181B1D4D6C4BEA7BE4B0713F0D378A2E2AA2C3000
```

It must also report `DOES NOT VERIFY` from `apksigner verify` before you sign it - that is the
expected state for an unsigned APK.

---

## 7. Source of the patches

The build is reproducible from the scripts in this repository:

```bash
python v51/patch_arsc.py      # builds v51/resources.patched.arsc from the baseline
python v51/pack_final.py      # emits v51/mojidict-9.1.1-final-unsigned.apk
```

See `README.md` for the full patch table.

---

## 8. Disclaimer

For personal study and local debugging only. The upstream application is the property of its
publisher; this project is not affiliated with it. Do not redistribute the patched binary or use
it commercially. You are responsible for complying with the laws that apply to you.
