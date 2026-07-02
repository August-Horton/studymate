import sqlite3

conn = sqlite3.connect('studymate.db')
conn.execute('ALTER TABLE notes ADD COLUMN folder VARCHAR DEFAULT "默认笔记本"')
conn.commit()
conn.close()
print('✨ 文件夹字段添加成功！')
