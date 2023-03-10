import numpy as np
from os import listdir
from os.path import isfile, join
from braincoordinator.utilities.computations import *
import cv2

class Manager:
    def __init__(self, animal_path, preload, reference):
        self.animal_path = animal_path
        try:
            self.slices = [file_name for file_name in listdir(self.animal_path) if isfile(join(self.animal_path, file_name))]
        except:
            raise FileNotFoundError

        self.coronals = []
        self.sagittals = []
        self.resize_factor = 1
        self.coronal_index = 0
        self.sagittal_index = 0
        self.reference = reference
        self.screen_width = 1920 #default
        self.interpolation=cv2.INTER_AREA #cv2.INTER_NEAREST#cv2.INTER_LANCZOS4


        self.parse_slices()

        self.get_native_sizes()
        self.get_tkt_scalar()



        self.preload = int(preload)
        if self.preload == 1:
            self.load_images()

        self.retrieve_coronal_scale()
        self.retrieve_sagittal_scale()

        self.load_abbr()


    def get_native_sizes(self):
        coronal_tuple = self.coronals[0]

        if coronal_tuple[1] != "":
            coronal_str = "b" + coronal_tuple[0] + "a" + coronal_tuple[1]
        else:
            coronal_str = "b" + coronal_tuple[0]

        coronal_image = cv2.imread(self.animal_path+"/{}.jpg".format(coronal_str), cv2.IMREAD_UNCHANGED)
        self.coronal_size = coronal_image.shape[:-1]

        ml = self.sagittals[self.sagittal_index]
        sagittal_image = cv2.imread(self.animal_path+"/l{}.jpg".format(ml))
        self.sagittal_size = sagittal_image.shape[:-1]

    def get_tkt_scalar(self):
        #1920 width default
        max_image_width = self.sagittal_size[1] + self.coronal_size[1]

        if self.screen_width * .8 < max_image_width:
            self.scale_factor = round(self.screen_width * .8/max_image_width * .935, 3)

            #self.new_sagittal_size = (int(self.sagittal_size[1] * self.screen_scalar), int(self.sagittal_size[0] * self.screen_scalar))
            #self.new_coronal_size = (int(self.coronal_size[1] * self.screen_scalar), int(self.coronal_size[0] * self.screen_scalar))


    def to_pixel(self, marker, type):

        if type ==0:
            #sagittal mm -> frontal pixels
            output=int(marker[1] * self.coronal_ml[1] + self.coronal_ml[0]), int((marker[2]) * self.coronal_dv[1] + self.coronal_dv[0])

        else:
            output= int(-marker[0] * self.sagittal_ap[1] + self.sagittal_ap[0]), int((marker[2]) * self.sagittal_dv[1] + self.sagittal_dv[0])

        return output#[round(o/self.scale_factor) for o in output]


    def to_pixel_r(self, marker, type):

        if type ==0:
            #sagittal mm -> frontal pixels
            output=int(marker[1] * self.coronal_ml[1] + self.coronal_ml[0]), int((marker[2]) * self.coronal_dv[1] + self.coronal_dv[0])

        else:
            output= int(-marker[0] * self.sagittal_ap[1] + self.sagittal_ap[0]), int((marker[2]) * self.sagittal_dv[1] + self.sagittal_dv[0])

        return [round(o/self.scale_factor) for o in output]

    def update_marker(self, marker, point, hover_window):
        marker[0] = point
        marker[2] = self.convert_to_mm(point, hover_window)


    def set_values(self, ap:float, ml:float, dv:float) -> None:

        vals = to_decimal(ap, ml, dv)
        self.ap, self.ml, self.dv = vals

        self.coordinate = vals[0], vals[1]

    def next(self, type:str):
        if type == "coronal":
            if self.coronal_index < len(self.coronals) - 1:
                self.coronal_index += 1
            else:
                print("No more slices.")
        else:
            if self.sagittal_index < len(self.sagittals) - 1:
                self.sagittal_index += 1
            else:
                print("No more slices.")

    def previous(self, type:str):
        if type == "coronal":
            if self.coronal_index != 0:
                self.coronal_index -= 1
            else:
                print("No more slices.")
        else:
            if self.sagittal_index != 0:
                self.sagittal_index -= 1
            else:
                print("No more slices.")

    def get_images(self):
        coronal_tuple = self.coronals[self.coronal_index]
        ml = self.sagittals[self.sagittal_index]

        self.coordinate = coronal_tuple[self.reference], ml

        if self.preload == 1:
            coronal_image = self.coronal_images[self.coronal_index].copy()
            sagittal_image = self.sagittal_images[self.sagittal_index].copy()

        else:

            if coronal_tuple[1] != "":
                coronal_str = "b" + coronal_tuple[0] + "a" + coronal_tuple[1]
            else:
                coronal_str = "b" + coronal_tuple[0]

            coronal_image = cv2.imread(self.animal_path+"/{}.jpg".format(coronal_str), cv2.IMREAD_UNCHANGED)
            if self.resize_factor != 1:
                size = coronal_image.shape
                coronal_image = cv2.resize(coronal_image, None, fx=self.resize_factor, fy=self.resize_factor, interpolation = self.interpolation)

            sagittal_image = cv2.imread(self.animal_path+"/l{}.jpg".format(ml), cv2.IMREAD_UNCHANGED)
            if self.resize_factor != 1:
                size = sagittal_image.shape

                sagittal_image = cv2.resize(sagittal_image, None, fx=self.resize_factor, fy=self.resize_factor,interpolation = self.interpolation)

        return cv2.cvtColor(coronal_image, cv2.COLOR_BGR2RGB), cv2.cvtColor(sagittal_image, cv2.COLOR_BGR2RGB)

    def convert_to_mm(self, marker, type:int) -> np.ndarray:

        #marker = [round(m/self.scale_factor) for m in marker]


        if type == 0: #ap
            raw_array = [str_to_float(self.coronals[self.coronal_index][0]), (marker[0] - self.coronal_ml[0])/self.coronal_ml[1], (marker[1] - self.coronal_dv[0])/self.coronal_dv[1]]
        else: #ml
            raw_array = [-(marker[0] - self.sagittal_ap[0])/self.sagittal_ap[1], str_to_float(self.sagittals[self.sagittal_index]), (marker[1] - self.sagittal_dv[0])/self.sagittal_dv[1]]

        return np.round(np.array(raw_array), 2)

    def convert_to_pixels(self, marker) -> np.ndarray:

        raw_array = [-(marker[0] * self.sagittal_ap[1] - self.sagittal_ap[0]), -(marker[1] * self.coronal_ml[1] - self.coronal_ml[0]), -(marker[2] * self.sagittal_dv[1] - self.sagittal_dv[0])]

        return np.array(raw_array, dtype=int)

    def find_nearest_value(self, array:np.ndarray, value:float) -> int:
        index = (np.abs(array - value)).argmin()
        return index

    def find_nearest_slices(self, coordinate = None) -> tuple:

        if coordinate == None:
            coordinate = self.coordinate

        split_float = np.delete(np.array(self.coronals), int(self.reference==0), 1)

        split_float = np.array([str_to_float(coronal_str[0]) for coronal_str in split_float])
        nearest_coronal = self.find_nearest_value(split_float, float(coordinate[0]))

        split_float = np.array([str_to_float(sagittal_str) for sagittal_str in self.sagittals])
        nearest_sagittal = self.find_nearest_value(split_float, float(coordinate[1]))

        return nearest_coronal, nearest_sagittal

    def load_images(self):
        self.coronal_images = np.zeros(len(self.coronals), dtype=object)
        self.sagittal_images = np.zeros(len(self.sagittals), dtype=object)

        print("Preloading images..")

        for index, _ in enumerate(self.coronals):
            coronal_tuple = self.coronals[index]

            if coronal_tuple[1] != "":
                coronal_tuple_str = "b" + coronal_tuple[0] + "a" + coronal_tuple[1]
            else:
                coronal_tuple_str = "b" + coronal_tuple[0]

            coronal_image = cv2.imread(self.animal_path+"/{}.jpg".format(coronal_str), cv2.IMREAD_UNCHANGED)

            if self.resize_factor != 1:
                size = coronal_image.shape
                coronal_image = cv2.resize(coronal_image, (int(size[1]*self.resize_factor),int(size[0]*self.resize_factor)),interpolation=self.interpolation)
            self.coronal_images[index] = coronal_image

            print("Loading coronal {}/{}".format(index, len(self.coronals) - 1))

        for index, _ in enumerate(self.sagittals):
            sagittal_slice = self.sagittals[index]
            sagittal_image = cv2.imread(self.animal_path+"/l{}.jpg".format(agittal_slice))

            if self.resize_factor != 1:
                size = sagittal_image.shape

                sagittal_image = cv2.resize(sagittal_image, (int(size[1] * self.resize_factor), int(size[0] * self.resize_factor)), interpolation=self.interpolation)

            print("Loading sagittal {}/{}".format(index, len(self.sagittals) - 1))
            self.sagittal_images[index] = sagittal_image

        print("Preloading succeeded")


    def parse_slices(self) -> None:
        for slice in self.slices:

            if slice[len(slice)-4:] != ".jpg":
                continue

            slice = slice[:-4] #remove .jpg

            if slice[0] == "l": #lateral/ml
                slice = slice[1:]
                self.sagittals.append(slice)
            else: #ap
                if "a" in slice:
                    slice = slice[1:]
                    split = slice.split("a") #[0] = bregma; [1] = lambda
                    self.coronals.append(split)
                else:
                    slice = slice[1:]
                    self.coronals.append([slice, ""])

        self.sagittals = sorted(self.sagittals, key=lambda x: float(x))
        self.coronals = sorted(self.coronals, key=lambda x: float(x[0]))


    def retrieve_coronal_scale(self):
        #ml
        filepath = self.animal_path + '/coronal_ml.sc'
        self.coronal_mls = []
        with open(filepath) as fp:
           line = fp.readline()
           while line:
               split = line.split(",")
               split = np.array(split, dtype = int) * self.scale_factor#resize_factor
               self.coronal_mls.append(split)
               line = fp.readline()

        filepath = self.animal_path + '/coronal_dv.sc'
        self.coronal_dvs = []

        with open(filepath) as fp:
           line = fp.readline()
           while line:
               split = line.split(",")
               split = np.array(split, dtype = int) * self.scale_factor#esize_factor
               self.coronal_dvs.append(split)
               line = fp.readline()

    def retrieve_sagittal_scale(self):#todo: fix sagittal/coronal naming

        filepath = self.animal_path+'/sagittal_ap.sc'
        self.sagittal_aps = []

        with open(filepath) as fp:
           line = fp.readline()
           while line:
               split = line.split(",")
               split = np.array(split, dtype = int) * self.scale_factor
               self.sagittal_aps.append(split)
               line = fp.readline()


        self.sagital_aps_txt = self.sagittal_aps.pop().astype(int)
        self.sagittal_aps = np.array(self.sagittal_aps, dtype=int)

        filepath = self.animal_path + '/sagittal_dv.sc'
        self.sagittal_dvs = []

        with open(filepath) as fp:
           line = fp.readline()
           while line:
               split = line.split(",")
               split = np.array(split, dtype = int) * self.scale_factor
               self.sagittal_dvs.append(split)
               line = fp.readline()

        self.sagital_dvs_txt = self.sagittal_dvs.pop().astype(int)
        self.sagittal_dvs = np.array(self.sagittal_dvs, dtype=int)
    #    self.sagittal_dvs=np.array(self.sagittal_dvs)
    #    ll=np.concatenate((np.flip(self.sagittal_dvs[1:],axis=0),self.sagittal_dvs))
    #    for l in ll:
    #        print("{},{}".format(l[0],l[1]))


    def set_scale(self) -> None:

        self.coronal_ml = self.coronal_mls[self.coronal_index]
        self.coronal_dv = self.coronal_dvs[self.coronal_index]

        self.sagittal_ap = self.sagittal_aps[self.sagittal_index]
        self.sagittal_dv = self.sagittal_dvs[self.sagittal_index]

    def load_abbr(self):
        filepath = self.animal_path + '/abbreviations.txt'
        self.abbreviations = []

        with open(filepath) as fp:
           line = fp.readline()
           while line:
               split = line.split(" ")
               abbreviation = split[0]
               if abbreviation != "\n":
                   description = " ".join(split[1:])
                   description = description.replace("\n", "")
                   self.abbreviations.append({"abbreviation" : abbreviation, "description" : description})

               line = fp.readline()

        self.abbreviations=sorted(self.abbreviations, key=lambda k: k['abbreviation'].lower())
