from setuptools import setup, find_packages

setup_requirements = ['pytest-runner']
install_requirements = ['regex']
test_requirements = ['pytest']
dev_requirements = []

setup(
    name='pysubconv',
    packages=find_packages(),

    setup_requires=setup_requirements,
    install_requires=install_requirements,
    tests_require=test_requirements,
    extras_require={
        'test': test_requirements,
        'dev': dev_requirements
    }
)