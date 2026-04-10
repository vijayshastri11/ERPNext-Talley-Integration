from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="erpnext_tally_sync",
    version="1.0.0",
    description="ERPNext ↔ Tally Prime two-way accounting sync",
    author="AVS Technologies Pvt. Ltd.",
    author_email="admin@avstechnologies.in",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
