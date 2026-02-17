# DSKY Integration Requirements (Anyware/GUI)

- Button 文本只能左上角显示，不可居中且不支持多行，不利于复现仪表类界面。
- 缺少 Button 文本的尺寸/对齐控制项，不利于做统一布局规范。
- SegmentDisplay 没有全局字号/缩放级别，不利于在不同分辨率下快速调整。
- SegmentDisplay 缺少统一风格/主题设置，不利于批量修改显示风格。
- 缺少文本宽度/高度测量能力，不利于做精确居中与对齐。
- PageStack 机制存在但未接入 AnywareApp，不利于多页面管理。
- AnywareApp 的 pop_page 为空实现，不利于页面栈回退。
- 缺少调试用的“全局配色简化”开关，不利于快速排错与对齐。
- 文档未清楚写明 Button 文本对齐/多行限制，不利于新用户理解布局能力边界。
- 文档未给出 SegmentDisplay 的推荐尺寸与密度范围，不利于快速设定可读性。
