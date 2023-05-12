from slyme import SlymeDriver

def main():

    profile_name = 'Default'
    slyme = SlymeDriver(pfname=profile_name, debug=True)
    input('Press ENTER to exit')

    slyme.end_session()

if __name__ == "__main__":
    main()
