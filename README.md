# MOJi 9.1.1 Local Modification Records (dev branch)

_PS: This branch only stores analysis scripts, patch generators, and reports._
_It does not contain binary artifacts such as APKs or DEX files._

- Baseline: `com.mojixxx.mojixxxx` v1742 (9.1.1), original APK 168,579,643 B (not included)
- Final product: `MOJiDict-9.1.1-final-debug-signed.apk` (163.88 MB, not included)
- SHA-256: `67840C60F29E274571E6C7DAEE01E4F8D83928061824E0EAAD413D1FFEC0D7C9`
- Package signature: Android Debug (`CN=Android Debug, O=Android, C=US`), cert SHA-256 `353c31b8b2ab10a675946d0079c5c64c35a35312bd70012eb7b32370b262e31e`

## Directory structure

Each path is listed once, with the purpose of that file or folder.

<table>
  <thead>
    <tr><th>Path</th><th>Purpose</th></tr>
  </thead>
  <tbody>
    <tr><td><code>arsc.py</code> / <code>axml.py</code> / <code>dex.py</code> / <code>dexl.py</code> / <code>trace2.py</code></td><td>ARSC / AXML / DEX parsing and patching</td></tr>
    <tr><td><code>v51/pack_final.py</code></td><td>Final packer (13 DEX/ARSC patches, emits an unsigned APK)</td></tr>
    <tr><td><code>v51/patch_arsc.py</code></td><td>ARSC equal-length string replacement (AI points label to infinity glyph)</td></tr>
    <tr><td><code>v51/patch_js_v53.py</code></td><td>H5 bundle permissionLimit patch (currently inert, kept for reference)</td></tr>
    <tr><td><code>v51/index-cc95ce0f.v53.js</code></td><td>Input asset for pack_final.py (patched local H5 bundle)</td></tr>
    <tr><td><code>patch/repack.py</code></td><td>APK repackaging helper</td></tr>
    <tr><td><code>patch/verify_patch.py</code></td><td>H5 patch verifier</td></tr>
    <tr><td><code>patch/frida_gate.js</code></td><td>Frida observation script for the gating flow</td></tr>
    <tr><td><code>REPORT_*.md</code></td><td>Stage reports; <code>REPORT_FINAL_2026-11-02.md</code> is the summary</td></tr>
  </tbody>
</table>

## Final patch overview

Thirteen DEX/ARSC patches, plus one inert H5 asset patch (kept but of no effect).
Each file is listed once; all targets and changes for that file appear beneath it.

<table>
  <thead>
    <tr><th>File</th><th>Target</th><th>Change</th></tr>
  </thead>
  <tbody>
    <tr>
      <td rowspan="10"><code>classes3.dex</code></td>
      <td><code>Lk5/h;-&gt;d()</code></td>
      <td>Return <code>"activated"</code> (account status)</td>
    </tr>
    <tr>
      <td><code>Lk5/g;-&gt;c()</code></td>
      <td>Return <code>true</code> (isPro)</td>
    </tr>
    <tr>
      <td><code>Lk5/g;-&gt;a()</code></td>
      <td>Return <code>4070908800000L</code> (2099-01-01 expiry)</td>
    </tr>
    <tr>
      <td><code>account/b;-&gt;c()</code></td>
      <td>Return <code>true</code> (lifetime flag kept true, stacked with Pro)</td>
    </tr>
    <tr>
      <td><code>m6/d;-&gt;b()</code></td>
      <td>Return <code>true</code> (AI mnemonic module switch)</td>
    </tr>
    <tr>
      <td><code>Ly5/a;-&gt;f()</code></td>
      <td>Return <code>2</code> (H5 source mode; observed to route to the debug remote, kept as neutral)</td>
    </tr>
    <tr>
      <td><code>MainMineFragment;-&gt;refreshVipCard</code> units 0x19/0x1a</td>
      <td><code>if-eqz v2,+88</code> -&gt; <code>goto +88</code> + <code>nop</code> (skips the lifetime branch)</td>
    </tr>
    <tr>
      <td><code>ReciteActivity$a;-&gt;done</code> unit 0x28</td>
      <td><code>const/16 10</code> -&gt; <code>999</code> (A/B group fallback cap)</td>
    </tr>
    <tr>
      <td><code>ReciteFinishActivity$a;-&gt;done</code> unit 0x28</td>
      <td><code>const/16 10</code> -&gt; <code>999</code></td>
    </tr>
    <tr>
      <td><code>MainMineFragment;-&gt;initObserver$lambda$36</code> units 0x09-0x0c, 0x17-0x1a</td>
      <td>Wallet MO coin / MO point reads replaced by <code>const/16 9999</code></td>
    </tr>
    <tr>
      <td><code>classes2.dex</code></td>
      <td><code>com/google/gson/internal/c;-&gt;p()</code></td>
      <td>Return <code>true</code> (membership check used by the Gson layer)</td>
    </tr>
    <tr>
      <td rowspan="2"><code>resources.arsc</code></td>
      <td><code>ai_point_entry_without_amount</code></td>
      <td>Label text replaced by an infinity glyph (equal byte length, 6 B)</td>
    </tr>
    <tr>
      <td><code>ai_point_entry</code></td>
      <td>Numeric format replaced by an infinity glyph variant (equal byte length, 10 B)</td>
    </tr>
    <tr>
      <td><code>assets/h5hybrid/assets/index-cc95ce0f.js</code></td>
      <td><code>permissionLimit</code> checks</td>
      <td>Made always true, counters set to 999 (INERT: the app loads the remote bundle)</td>
    </tr>
  </tbody>
</table>

## Build-by-Yourself (original APK required)

1. Place the original APK at `build/mojidict-9.1.1-src.apk`.
2. Run `python v51/patch_arsc.py` to generate `v51/resources.patched.arsc`.
3. Run `python v51/pack_final.py` to generate `v51/mojidict-9.1.1-final-unsigned.apk`.
4. Run `zipalign -p -f 4` and then `apksigner sign --ks <keystore>`.

Signing keys are not stored in this repository. Use your own keystore or the default Android debug keystore (password `android`).

## Unfinished / known limitations

- Enforced server-side; client patches cannot bypass them:
  - Favorite-count limits
  - Memorization quotas
  - Entry-detail data
  - AI content
  - e.t.c.
- Forcing the local H5 bundle failed: DEX string pools must stay sorted by UTF-16 order, and in-place rewriting breaks that order, producing `ClassNotFoundException`.
- MITM(for deceptive input): requires a system-level CA (Android 14+ keeps system CAs in the conscrypt APEX) and has not been implemented temporarily.
- Numeric fields such as AI points are rendered by the remote H5, so client-side value patches only affect native display sites.

## Statement

**For personal study and local debugging only. Do not redistribute the modified binary.**
