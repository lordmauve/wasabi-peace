from setuptools import setup

setup(
    name='bitsofeight',
    version='0.0.1',
    description="Melee on the high seas",
    long_description=open('README.rst').read(),
    author='Wasabi Peace',
    author_email='',
    url='https://bitbucket.org/lordmauve/wasabi-peace',
    packages=['bitsofeight'],
    install_requires=[
        'numpy',
        'pyglet==1.2alpha1',
        'wasabi-scenegraph',
    ],
    dependency_links=[
        'http://code.google.com/p/pyglet/downloads/list',
    ],
    zip_safe=False,
    package_data={
        'assets': '*',
    },
    entry_points={
        'console_scripts': [
            'bitsofeight = bitsofeight.game:main',
        ],
    }
)
