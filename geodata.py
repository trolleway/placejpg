#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse

from model_geo import Model_Geo



parser = argparse.ArgumentParser(
    description="make photo coordinates file")


parser.add_argument('-path', type=str,  default='i')
parser.add_argument('-output', type=str,  default='photos.geojsonl')
parser.add_argument('-depth0', action='store_true',help='only top directory')


if __name__ == '__main__':
    
    args = parser.parse_args()
    modelgeo = Model_Geo()

    modelgeo.make_photo_coordinates_file(args.path, args.output, args.depth0)
    
    
    