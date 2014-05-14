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
        #'numpy',
        'pyglet==1.2alpha1',
        'wasabi-lepton==1.0b2',
        'PyOpenGL==3.0.2',
        'pyglet>=1.2alpha1',
        'euclid>=0.1',
    ],
    dependency_links=[
        'http://code.google.com/p/pyglet/downloads/list',
    ],
    zip_safe=False,
    package_data={
        'assets': '*',
        'lib':'*.dll',
    },
    entry_points={
        'console_scripts': [
            'bitsofeight = bitsofeight.game:main',
        ],
    }
)
