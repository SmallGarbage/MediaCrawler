import argparse
import config


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices=["xhs", "dy", "ks", "bili", "wb"], type=str, default=config.PLATFORM,
                        help="Media platform select (xhs | dy | ks | bili | wb)")
