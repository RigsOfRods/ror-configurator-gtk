# setup.py
setup(
    name='Rigs of Rods Configurator (GTK+)',
    version=__version__,
    long_description=markdown_contents,
    packages=['ror-configurator-gtk'],
    entry_points={
        'console_scripts': ['ror-configurator-gtk=ror-configurator-gtk:main']
    }
)
