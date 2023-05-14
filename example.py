from slyme import SlymeDriver
import time

def main():

    slyme = SlymeDriver(pfname='Default')
    time.sleep(5)
    slyme.select_latest_chat()
    time.sleep(5)
    

    while True:
        prompt = input('Input a prompt:  ')
        if prompt == '':
            break
        output = slyme.completion(prompt)
        print(output)

    slyme.end_session()

if __name__ == "__main__":
    main()
