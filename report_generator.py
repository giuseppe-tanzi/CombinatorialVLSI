import argparse
from glob import glob
import pandas as pd
import os

def extract_info(file):
    info = {}
    last = False
    for row in file:
        if "propagators" in row:
            info['Propagators'] = row[25:].replace("\n","")
        elif "propagations" in row:
            info['Propagations'] = row[26:].replace("\n","")
        elif "failures" in row:
            info['Failures'] = row[22:].replace("\n","")
        elif "restarts" in row:
            info['Restarts'] = row[22:].replace("\n","")
        elif "Height" in row:
            info['Height'] = int(row[8:].replace("\n",""))
        elif "====" in row:
            last = True
        elif last:
            info['Time'] = float(row).__round__(3)
    return info


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out_dir",
                        help="Path to the directory that contains the output solutions in .txt format",
                        required=False, type=str, default=".\\out\\final")
    args = parser.parse_args()


    outputs = glob(os.path.join(args.out_dir, "ins-*"))

    df = pd.DataFrame(columns=['Failures','Restarts','Propagators','Propagations','Height','Time','Instance'])
    for output in outputs:
        with open(output, 'r') as f:
            current_instance = extract_info(f)
            if current_instance != {}:
                current_instance['Instance'] = output[output.find("ins-")+4:output.find("-out")]
                df = df.append(current_instance, ignore_index=True)

    df.to_csv(os.path.join(args.out_dir, "report.csv"))


if __name__ == '__main__':
    main()