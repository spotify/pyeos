from setuptools import setup, find_packages
from pip.req import parse_requirements


# parse_requirements() returns generator of pip.req.InstallRequirement objects
install_reqs = parse_requirements('requirements.txt')

# reqs is a list of requirement
# e.g. ['django==1.5.1', 'mezzanine==1.4.6']
reqs = [str(ir.req) for ir in install_reqs]

version = '0.5'

setup(
    name='pyEOS',
    version=version,
    py_modules=['pyEOS'],
    packages=find_packages(),
    install_requires=reqs,
    include_package_data=True,
    description = 'Python API to interact with network devices running EOS',
    author = 'David Barroso',
    author_email = 'dbarroso@spotify.com',
    url = 'https://github.com/spotify/pyeos/', # use the URL to the github repo
    download_url = 'https://github.com/spotify/pyeos/tarball/%s' % version,
    keywords = ['EOS', 'networking'],
    classifiers = [],
)
