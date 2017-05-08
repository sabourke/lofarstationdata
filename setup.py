from setuptools import setup, find_packages

description = "lofarstation: Work with XST, ACC and AARTFAAC data."
long_description = description

setup(
    name='lofarstationdata',
    author='Stephen Bourke',
    version=0.9,
    url='http://github.com/sabourke/lofarstation/',
    description=description,
    long_description=long_description,
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering :: Astronomy',
        'Topic :: Utilities',
        ],
    install_requires=['numpy', 'python-casacore'],
    packages=find_packages(exclude=['tests','examples']),
    package_data={'lofarstation': ['AntennaFields/*']},
    entry_points={
        'console_scripts': [
            'lofar-station-ms=lofarstation.converter:main',
        ],
    },
)
