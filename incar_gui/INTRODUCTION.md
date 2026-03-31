## Q-robot INCAR Generator

This tool is a Flask-based wrapper around the `brain.incars` library that lets you compose VASP INCAR files from standard sections, task presets, and ad-hoc parameters through a browser interface.  
该工具封装了 `brain.incars`，在浏览器中组合标准块、任务预设与自定义参数即可输出 VASP INCAR 文件。

### 1. Dependencies

- Install the Python prerequisites before starting by running `pip install -r requirements.txt` from the `incar_gui` directory; that brings in Flask/Werkzeug for the web server.  
- 在 `incar_gui` 目录下运行 `pip install -r requirements.txt` 即可安装 Flask/Werkzeug。  
- If you plan to use the POSCAR-aware helpers (DFT+U, MAGMOM guessing, etc.), install ASE as well (`pip install ase`) so those endpoints can read your structure file.  
- 若希望使用 POSCAR 自动推送 DFT+U、MAGMOM 等功能，请额外安装 ASE（`pip install ase`），以便相关接口可以读取结构。

### 2. Running the GUI

- From the root of the repo (`incar_gui`), launch the interface with `python app.py`.  
- 也可以先运行 `setup.sh`，脚本自动创建/激活 `venv` 并安装依赖，结束时会提示后续激活与运行命令。  
- The launcher prints a banner, opens `http://127.0.0.1:5001` in your browser, and starts the Flask server on that same address/port; you can override the host or port by setting `QROBOT_HOST`/`QROBOT_PORT` in your environment before running.  
- 启动后会打印横幅并自动打开浏览器连接 `127.0.0.1:5001`，也可以通过 `QROBOT_HOST`/`QROBOT_PORT` 自定义绑定地址/端口。  
- Once the page loads, the categories, standard sections, and task buttons populate from the JSON configuration.  
- 页面加载完毕后，分类、标准参数块和任务按钮会自动从 JSON 配置中填充。

### 3. DIY Personal INCAR Generator

- `incar_gui/task_config.json` contains the category hierarchy plus the default parameter dictionaries for every button. Add, rename, or adjust entries under “Functional”, “Correction”, “Model”, “System”, and “Tasks” to expose your own workflows, and the UI and generation logic will automatically pick up the new settings next time you load the page.  
- 通过修改 `incar_gui/task_config.json` 中的 “Functional”、 “Correction” 等字典，可以添加、重命名或替换任务，前端与 INCAR 生成逻辑会自动使用这些变更。  
- `incar_gui/app.py` ties those categories to the frontend, defines the `/api/task-params` and `/api/generate-incar` endpoints, and renders the template. If you need new API behaviors (e.g., extra validation, new computed sections, or different grouping rules), modify the Flask routes here and refresh the browser to try them out.  
- `incar_gui/app.py` 将这些分类绑定到前端，提供 `/api/task-params`、`/api/generate-incar` 等路由并渲染模板；想要增加校验规则、拓展生成逻辑或重新分组，只需在此调整 Flask 路由并刷新浏览器即可。
