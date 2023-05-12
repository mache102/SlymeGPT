from slyme import SlymeDriver

def main():

    slyme = SlymeDriver(pfname='Default')
    slyme.select_latest_chat()

    while True:
        prompt = input('Input a prompt:  ')
        if prompt == '':
            break
        output = slyme.completion(prompt)
        print(output)

    slyme.end_session()

if __name__ == "__main__":
    main()
