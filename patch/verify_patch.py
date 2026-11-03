import os, re, sys

PATCHED = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index-cc95ce0f.js')
ORIG    = r'D:\Downloads\MiShare\v9.1.1\assets\h5hybrid\assets\index-cc95ce0f.js'

a = open(ORIG, 'rb').read()
b = open(PATCHED, 'rb').read()
print('orig bytes    :', len(a))
print('patched bytes :', len(b), '| 同尺寸:', len(a) == len(b))

t = b.decode('utf-8', 'surrogateescape')
# 期望计数说明：S2 为 2，是因为源码里本就有
#   (isMOJiTest||isMOJiRead)&&(ye.state.isPro=!0) 这条内置升权分支
checks = [
    ('S1 store 默认',  'isPro:!0',                 1),
    ('S2 pageConfig',  'ye.state.isPro=!0',        2),
    ('S3 教学例句 A',  'A=w(()=>!0)',              1),
    ('S4 释义 permit', 'P=w(()=>!0)',              1),
]
ok = True
for name, needle, want in checks:
    hit = t.count(needle)
    print('%-16s %-24r count=%d (expect %d)' % (name, needle, hit, want))
    ok = ok and hit == want
stale = [n for n, s in [('isPro:!1', 'isPro:!1'), ('ye.state.isPro=o.isPro', 'x')] if False]
print('残留原串 isPro:!1 :', t.count('isPro:!1'))
print('残留原串 isPro=o.isPro :', t.count('ye.state.isPro=o.isPro'))
print('残留原串 !! (l.value&&d.value) :', t.count('!!(l&&d.value)'), t.count('!!(l.value&&d.value)'))
print()
print('门控语义（补丁后）:')
print('  释义遮罩  !isPermission && !isPro  → false  → 遮罩不出现，渲染动作行')
print('  动作行    「更多例句」→ navigateToMoreExamples / 「深度解析单词」→ navigateToDeepWordAnalysis')
print('  教学例句  A = 登录 && Pro → true')
print('            showTeachingMask = !isPopup && len>1 && !A → false')
print('            displaySentences = isPopup || A ? 全量 : 第1条 → 全量')
print('            onClickMore      = !A ? 付费墙 : showTeachingSentencePopup → 弹窗')
print('RESULT:', 'PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)
