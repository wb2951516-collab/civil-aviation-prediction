# CAPM.exe Windows 版本资源（右键属性 → 详细信息可见，用于核对安装版本）。
# 注意：本文件由 PyInstaller 以 eval 解析，只允许注释 + 单一 VSVersionInfo 表达式，
# 不要加 coding 声明或 docstring。发布新版本时同步 filevers / FileVersion / ProductVersion。

VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=(1, 4, 0, 0),
        prodvers=(1, 4, 0, 0),
        mask=0x3F,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0),
    ),
    kids=[
        StringFileInfo(
            [
                StringTable(
                    "080404b0",
                    [
                        StringStruct("CompanyName", "SuperM"),
                        StringStruct("FileDescription", "民航旅客运输量预测系统"),
                        StringStruct("FileVersion", "1.4.0"),
                        StringStruct("InternalName", "CAPM"),
                        StringStruct("LegalCopyright", "Copyright (C) 2026 SuperM"),
                        StringStruct("OriginalFilename", "CAPM.exe"),
                        StringStruct("ProductName", "CAPM 民航旅客运输量预测系统"),
                        StringStruct("ProductVersion", "1.4.0"),
                    ],
                )
            ]
        ),
        VarFileInfo([VarStruct("Translation", [2052, 1200])]),
    ],
)
