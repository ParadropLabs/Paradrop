from flask import Flask

def run():
    app = Flask(__name__)

    @app.route('/')
    def hello_world():
        return 'hello world!'

    #assign to eth0 dynamically (or run it )
    # app.run('10.0.2.15', port = 7777)

    #running locally
    #TODO: determine if running locally or on snappy 
    app.run(port = 7777)

def main():
    #I have a haunting feeling this is not the correct way of doing things
    print 'Starting Main'
    run()

if __name__ == "__main__":
    main()

'''
To be clear, this works with pex. Install this package and run the following:
sudo pex flask spack -o out.pex -e spack:main

'''