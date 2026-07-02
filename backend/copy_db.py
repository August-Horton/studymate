import shutil
import os

src = 'studymate.db'
dst = 'data/studymate.db'

if os.path.exists(src):
    print(f'正在复制数据库从 {src} 到 {dst}...')
    shutil.copy2(src, dst)
    print('✅ 数据库复制成功！')
else:
    print(f'⚠️ 源数据库 {src} 不存在')
