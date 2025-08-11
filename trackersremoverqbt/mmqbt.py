import macmenuqbt.core as mmqbt
import sys


def main():
    # Récupérer les arguments depuis la ligne de commande (exemple)
    args = sys.argv[1:]
    # Parse arguments ou hardcode ici
    host = args[0] if len(args) > 0 else "localhost"
    port = int(args[1]) if len(args) > 1 else 8080
    username = args[2] if len(args) > 2 else "admin"
    password = args[3] if len(args) > 3 else ""
    interval = int(args[4]) if len(args) > 4 else 1

    mmqbt.main(host, port, username, password, interval)


if __name__ == "__main__":
    main()
