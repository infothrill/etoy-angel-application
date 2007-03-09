

def main():
    import angel_app.proc.maintainer

    options = angel_app.proc.maintainer.boot()
    angel_app.proc.maintainer.dance(options)

if __name__ == "__main__":
    main()