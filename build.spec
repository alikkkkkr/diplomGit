# build.spec
block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['/Users/alinaryzhkova/PycharmProjects/DiplomProject'],
    binaries=[],
    datas=[
        ('DiplomProject/settings.py', 'DiplomProject'),  # Копируем settings.py
        ('doc/migrations/*', 'doc/migrations'),  # Миграции
        ('doc/models.py', 'doc'),  # Модели
    ],
    hiddenimports=[
        'django',
        'doc.apps.DocConfig',  # Конфиг приложения (из apps.py)
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Если нужно окно консоли
    onefile=True,
)