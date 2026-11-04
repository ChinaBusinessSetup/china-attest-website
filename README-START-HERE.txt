China Attest 网站完整源文件备份
日期：2026-11-04
已发布版本：68

打开方法：
1. 完整解压 ZIP，请勿在压缩软件内部直接打开页面。
2. 打开 ChinaAttest-Website/dist/index.html。
3. 保留全部文件及目录结构，Language 菜单可进入对应语言页面。

包含最新的页脚、服务名称、客户评论名称、多语言更新、城市页面及本地相对路径修复。
语言：英文、西语、法语、德语、葡语、俄语、阿拉伯语。

咨询表单提交、WhatsApp 与邮箱链接需要联网。表单发送建议使用已发布网站或本地 HTTP 预览。

本地 HTTP 预览（需要 Python）：
在 ChinaAttest-Website 文件夹打开终端并运行：
python3 -m http.server 8765 --directory dist
然后访问 http://localhost:8765/

维护翻译（需要 Python 和 lxml）：
python3 scripts/build-locales.py
python3 scripts/check-locales.py

完整文件包括 dist 页面与资源、翻译词库、维护脚本和现有托管配置。
不包含 Git 凭据、Git 历史或临时预览文件。
源代码版本：0d9ab3840e6885217bb8ebb08c327866bafc4379
