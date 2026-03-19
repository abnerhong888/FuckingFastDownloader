# FuckingFast Downloader
## for downloading fuckingfast clould space
# pip install
```bash
python -m pip install --upgrade pip
pip install requests selenium tqdm pyyaml pySmartDL
```

# Usage
```bash
# for get download link
python FunDownloader.py --url=<url>
# for get download list
python FunDownloader.py --list --url=<url>
# for append download list to existing yaml file
python FunDownloader.py --append=<yaml_file> --list --url=<url>
# for download
python downloader.py -l=links.yaml -c=config.yaml
```
