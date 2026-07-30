# 霞姐桌宠示例交付

此目录保留本次 Skill 的真实、可复现样例；角色图和动作资源已获仓库所有者授权存放于此私有仓库。

- `assets/raw/`：原始角色与动作图，保留作身份与修复参考。
- `assets/*.png`：透明背景的静态状态图。
- `assets/frames/`：待机、走路、挥手、摸头、投喂、睡眠六组逐帧 PNG，共 24 帧。
- `assets/animation_raw/`：生成后的原始动作条，供 `extract_animation_strip.py` 重提取。
- `main.py`：PySide6 桌宠主程序，默认使用舒缓稳定动画策略。
- `desktop_pet.spec`：PyInstaller 单文件 Windows 打包配置。
- `*_qa.py` 与处理脚本：抠图、动作条提取、视觉与动画检查辅助工具。

## Build

在安装 PySide6、Pillow、PyInstaller 的项目虚拟环境中，从此目录执行：

```powershell
python -m py_compile main.py
pyinstaller --noconfirm --clean desktop_pet.spec
```

构建产物会输出为 `dist/XiaJieDesktopPet.exe`。不要覆盖正在运行的 EXE；将其复制为新的发行文件名后再交付。

## Release

`../../releases/霞姐桌宠-舒缓稳定版.exe` 是已测试的舒缓稳定版，SHA-256：

`2FE1F9D8DD293FCFFFB1DB566D8DCF83A28E5242DB99EA144D2107C6908B702C`
