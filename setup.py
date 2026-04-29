from cx_Freeze import setup, Executable

build_exe_options = {
    "excludes": [],
    "zip_include_packages": ["scipy","pylablib","time","matplotlib","os","threading","PIL","simple_pyspin","sys","shutil","PyQt5","re","json","subprocess","typing","pandas","socket"],
}

setup(
    name="CamView",
    version="0.1",
    description="Tool to Control Cameras",
    options={"build_exe": build_exe_options},
    executables=[Executable("cli.py",base="console")],
)