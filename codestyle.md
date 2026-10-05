# 后端代码规范

本规范参考 Python 官方 [PEP 8](https://peps.python.org/pep-0008/) 和 [PEP 257](https://peps.python.org/pep-0257/)。

- 使用 4 个空格缩进，禁止 Tab。
- 每行尽量不超过 100 个字符；长表达式使用括号换行。
- 函数和变量使用 `snake_case`，类使用 `PascalCase`，常量使用 `UPPER_SNAKE_CASE`。
- 公共函数和模块写 docstring，类型明确时使用类型标注。
- 捕获异常时只捕获可以处理的具体异常，不使用裸 `except`。
- SQL 使用参数化占位符，不拼接用户输入。
- 业务逻辑、HTTP 处理和数据库访问分层，避免在处理器中复制计算逻辑。
