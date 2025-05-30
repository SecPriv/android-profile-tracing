from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import gzip
import tqdm
import click
import requests
import asyncio
import aiohttp

import xml.etree.ElementTree as ET

from gexplorer.Database import Database
from google_play_scraper.exceptions import NotFoundError
from google_play_scraper import app
from google_play_scraper import permissions

# Package names

def get_package_names(db_path: str, parallelism: int):
    """
        Retrieves all package names on the Google Play Store
    """
    db: Database = _get_db(db_path)
    xml_urls: list[str] = __retrieve_xml_urls()
    db.insert_sitemap_urls(xml_urls)
    newest_urls: list[str] = __get_relevant_xml_urls(db, xml_urls)
    asyncio.run(__async_get_package_names(db, newest_urls, parallelism))

async def __async_get_package_names(db: Database, newest_urls: list[str], parallelism: int):
    sem = asyncio.Semaphore(parallelism)
    async with aiohttp.ClientSession() as session:
        tasks = [__bounded_retrieve_package_names(url, session, sem) for url in newest_urls]
        for coro in tqdm.tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Retrieving package names"):
            result = await coro
            url, package_names = result
            db.add_success_package_names(url, package_names)

async def __bounded_retrieve_package_names(url, session, sem):
    async with sem:
        return await __retrieve_package_name(url, session)

async def __retrieve_package_name(url, session, tries=3):
    """
    Downloads a file from the given URL into the specified directory.
    Downloads are performed in streaming mode to handle large files.
    """
    href_values = []
    if (tries == 0):
        raise Exception("Failed to download file.")
    try: 
        async with session.get(url) as response:
            response.raise_for_status()  # Raise HTTPError for bad responses.
            content = await response.read()
            decompressed_data = gzip.decompress(content)
            xml_str = decompressed_data.decode('utf-8')
            root = ET.fromstring(xml_str)
            for elem in root.iter():
                href = elem.attrib.get('href')
                if href:
                    href_values.append(href)
        
    except Exception as e:
        await asyncio.sleep(10)
        return await __retrieve_package_name(url, session, tries - 1)
    
    unique_href_values = set(href_values)
    app_href_values = [href for href in unique_href_values if href.startswith('https://play.google.com/store/apps/details?id=')]
    package_names = [href.split('=')[-1] for href in app_href_values]
    return (url, package_names)

def __get_relevant_xml_urls(db: Database, xml_urls: list[str]):
    all_dates = []
    for url in xml_urls:
        date = url.split("https://play.google.com/sitemaps/play_sitemaps_")[1].split("_")[0]
        all_dates.append(date)
    all_dates = list(set(all_dates))
    newest_date = max(all_dates)
    newest_urls = [url for url in xml_urls if newest_date in url]
    unsuccessful_sitemap_urls = db.get_unsuccessful_sitemap_urls()
    unsuccessful_sitemap_set = set(unsuccessful_sitemap_urls)  # Convert to set for fast lookup
    relevant_urls = [url for url in newest_urls if url in unsuccessful_sitemap_set]
    return relevant_urls


def __retrieve_xml_urls():
    sitemap_xmls = []
    sitemap_index = 0

    while True:
        sitemap_url = f"https://play.google.com/sitemaps/sitemaps-index-{sitemap_index}.xml"
        response = requests.get(sitemap_url)
        if response.status_code == 404:
            # If no sitemap index is found, we have reached the end of the sitemap indexes
            break
        sitemap_xmls.append(response.content)
        sitemap_index += 1
    
    xml_urls = []
    for sitemap_xml in sitemap_xmls:
        root = ET.fromstring(sitemap_xml)
        # find all loc tags in the xml using xpath
        for loc in root.findall(".//*"):
            # Ignore namespaces by checking the local tag name
            if loc.tag.endswith("loc"):
                url = loc.text.strip()
                if url.endswith(".xml.gz"):
                    xml_urls.append(url)
    return xml_urls


# Details

def get_app_details(db_path: str, parallelism: int):
    """
    Fetches details for all the apps in the database.
    """
    db = _get_db(db_path)

    package_names = db.get_package_name_info_to_fetch()
    print(f"Fetching details for {len(package_names)} apps.")

    with ThreadPoolExecutor(max_workers=parallelism) as executor:
        future_to_package = {
            executor.submit(_get_app_detail, package_name): package_name 
            for package_name in package_names
        }
        try:

            for future in tqdm.tqdm(as_completed(future_to_package), total=len(future_to_package), desc="Fetching app details"):
                package = future_to_package[future]
                try:
                    result = future.result()

                    if (result is None):
                        # the package is not found
                        db.add_package_name_info(package, None, None, None, None, None, 404)
                    else:
                        package_name, free, min_installs, icon, json, permissions = result
                        db.add_package_name_info(package_name, free, min_installs, icon, json, permissions, 1)
                except Exception as e:
                    db.add_package_name_info(package, None, None, None, None, None, 500)
        except KeyboardInterrupt:
            print("Shutting down remaining tasks...")
            for future in future_to_package:
                future.cancel()
            executor.shutdown(wait=False)

def _get_app_detail(package_name):
    try:
        result = app(package_name,
            lang='en',
            country='at'
        )
        ps = permissions(
            package_name,
            lang='en',
            country='at'
        )

        min_installs = result.get('minInstalls')
        free: bool = result.get('free')
        icon = result.get('icon')
        json = result
        return (package_name, free, min_installs, icon, json, ps)
    except NotFoundError as e:
        return None

# Icons

def get_app_icons(db_path: str, output_dir: str, parallelism: int):
    """
        Downloads the icons of all apps identified by their package names in the database
        :param db_path: Path to the database file
        :param output_dir: Path to the output directory
    """
    db: Database = _get_db(db_path)
    tuples: list[str, str] = db.get_missing_icon_urls()

    # check if the output directory exists. If not, create it
    os.makedirs(output_dir, exist_ok=True)

    print(f"Downloading icons for {len(tuples)} apps.")
    asyncio.run(_async_get_app_icons(db, output_dir, tuples, parallelism))

async def _async_get_app_icons(db, output_dir, missing_tuples, parallelism):
    sem = asyncio.Semaphore(parallelism)
    async with aiohttp.ClientSession() as session:

        tasks = [asyncio.create_task(_bounded_get_image(url, output_dir, package_name, session, sem)) for package_name, url in missing_tuples]

        for task in tqdm.tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Downloading icons"):
            package_name, status = await task
            db.set_icon_status(package_name, status)

async def _bounded_get_image(url, output_dir, package_name, session, sem):
    async with sem:
        return await _get_image(url, output_dir, package_name, session)

async def _get_image(url, output_dir, package_name, session, tries=3):
    if tries == 0:
        return (package_name, 0)
    try: 
        async with session.get(url) as response:
            response.raise_for_status()  # Raise HTTPError for bad responses.
            # it is a png image that I want to save
            # check if it is a 404. 
            if response.status == 404:
                return (package_name, 404)

            content = await response.read()
            file_path = os.path.join(output_dir, f"{package_name}.png")
            with open(file_path, 'wb') as f:
                f.write(content)
            return (package_name, 1)
    except Exception as e:
        await asyncio.sleep(10)
        return await _get_image(url, output_dir, package_name, session, tries - 1)

def _get_db(path: str) -> Database:
    return Database(path)


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())

@click.command("crawl")
@click.option("--db", "db_path", help="Path to the database file")
@click.option("--parallelism", "parallelism", default=10, help="Number of parallel requests")
@click.option("--details", "get_details", is_flag=True, help="Fetch details for all package names")
@click.option("--icons", "get_icons", is_flag=True, help="Download icons for all package names")
@click.option("--icon-out", "icon_out", help="Output directory for icons")
def crawl(db_path, parallelism, get_details, get_icons, icon_out):
    """
        Retrieves a list of all package names on the Google Play Store
    """
    get_package_names(db_path, parallelism)
    if get_details:
        get_app_details(db_path, parallelism)
    if get_icons:
        get_app_icons(db_path, icon_out, parallelism)

cli.add_command(crawl)

