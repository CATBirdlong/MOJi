// moji 9.1.1 - keep the "view all definitions and examples" and "view all teaching examples"
// entry points flowing into their functional branches instead of showing a paywall.
// Goal: make the local gate state read as authorized (isPro / permission true).
// Usage: frida -U -f com.mojixxx.mojixxxx -l frida_gate.js --no-pause
//        or frida -U com.mojixxx.mojixxxx -l frida_gate.js

Java.perform(function () {
  send('[gate] attach');

  // ---------------------------------------------------------------
  // 1) Unified membership check: the H5 isPro injection and the desktop
  //    widget gate share this function.
  //    WordDetailFragment: map.put("isPro", account.b.b().e().c())
  //    MojiWidget.g:       if (com.google.gson.internal.c.p())  -> content branch
  // ---------------------------------------------------------------
  try {
    var C = Java.use('com.google.gson.internal.c');
    C.p.overload().implementation = function () { return true; };
    send('[gate] hook com.google.gson.internal.c.p() -> true');
  } catch (e) { send('[gate] c.p hook failed: ' + e); }

  // ---------------------------------------------------------------
  // 2) Fallback: rewrite the pageConfig HashMap directly (isPro / userId).
  //    Useful when c.p is inlined or renamed by obfuscation.
  // ---------------------------------------------------------------
  try {
    var W = Java.use('com.mojitec.mojidict.widget.f');
    var Boolean_ = Java.use('java.lang.Boolean');
    W.e0.overloads.forEach(function (ov) {
      if (ov.argumentTypes.length !== 3) return;
      ov.implementation = function (a, b, c) {
        try {
          if (b !== null) {
            b.put('isPro', Boolean_.$new(true));
            b.put('userId', Java.use('java.lang.String').$new('local-pro'));
            b.put('aiMemory', Boolean_.$new(true));
          }
        } catch (e) { send('[gate] map patch: ' + e); }
        return ov.call(this, a, b, c);
      };
      send('[gate] hook widget.f.e0(' + ov.argumentTypes.join(',') + ')');
    });
  } catch (e) { send('[gate] e0 hook failed: ' + e); }

  // ---------------------------------------------------------------
  // 3) Push pageConfig once the page is ready - the closest equivalent of
  //    "always injecting isPro". window.updateHTML accepts an object or a
  //    base64 string, routed by case "pageConfig" -> setPageConfig.
  // ---------------------------------------------------------------
  try {
    var WebView = Java.use('android.webkit.WebView');
    var payload = JSON.stringify({
      settings: [{
        type: 'pageConfig',
        data: { isPro: true, userId: 'local-pro', platform: 'android', preferredLanguage: 'zh-Hans' }
      }]
    });
    var js = 'javascript:window.updateHTML(' + payload + ')';
    WebView.loadUrl.overload('java.lang.String').implementation = function (u) {
      this.loadUrl(u);
      if (u && u.indexOf('contentDetails_v2') >= 0) {
        var self = this;
        setTimeout(function () {
          Java.scheduleOnMainThread(function () {
            try { self.evaluateJavascript(js, null); send('[gate] pageConfig pushed'); }
            catch (e) { send('[gate] evaluateJavascript: ' + e); }
          });
        }, 900);
      }
    };
    send('[gate] WebView.loadUrl hook ready');
  } catch (e) { send('[gate] WebView hook failed: ' + e); }
});
