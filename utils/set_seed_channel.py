import sys
import yaml

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: {} <path> <snap_name> <channel>".format(sys.argv[0]))
        sys.exit(1)

    path = sys.argv[1]
    snap_name = sys.argv[2]
    channel = sys.argv[3]

    with open(path, 'r') as source:
        seed = yaml.safe_load(source)

    for snap in seed['snaps']:
        if snap['name'] == snap_name:
            print("Changed snap {} channel {} to {}".format(snap_name,
                snap.get('channel', None), channel))
            snap['channel'] = channel

    with open(path, 'w') as output:
        yaml.dump(seed, output)
