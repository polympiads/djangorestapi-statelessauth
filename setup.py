import setuptools

install_requires = open("requirements.txt", "r").readlines()

setuptools.setup(
    name="rest_framework_statelessauth",
    version="1.0.0",
    author="Polympiads",
    description="Django Rest Framework Stateless Auth",
    install_requires=install_requires,
    url="https://github.com/polympiads/djangorestapi-statelessauth",
    packages=["rest_framework_statelessauth"]
)