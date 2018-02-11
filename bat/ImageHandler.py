import logging

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from PIL import ImageFilter
from PIL import ImageDraw

from bat.DicomHandler import DicomHandler


class ImageHandler(DicomHandler):
    """
    ImageHandler class is a heritage of DicomHandler class.
    The ImageHandler class can provide more functions based on the DicomHandler class.
    """
    def __init__(self, filename):
        """
        Initialization function
        :param filename: input dicom file name including path
        """
        self.isImageComplete = False
        # self.RescaleType = {'linear', 'gamma'}
        try:
            # call super to init DicomHandler class first
            super(self.__class__, self).__init__(filename)
        except Exception as e:
            logging.error(str(e))
        if not self.isComplete:
            logging.warning(r"Dicom class initialed failed. Procedure quited.")
            return

        try:
            # Convert to HU unit
            self.ImageHU = self.RawData * self.Slop + self.Intercept
            self.ImageRaw = self.ImageHU.copy()
            # calculate first time that can show image according pre-set windowing
            self.rescale_image((50, 0))
            # center is always in format (row, col)
            # Radius is always in format (radius in pixel, radius in cm)
            self.Center, self.Radius = self.calc_circle()
            self.Center=(256,256)
            # define circular integration result
            self.Image_Integration_Result = np.zeros(self.Radius[0])
            self.Image_Median_Filter_Result = np.zeros(self.Radius[0])
            # main calculation
            self.integration()
        except Exception as e:
            logging.error(str(e))
            return
        # set the flag to indicate initializing done
        self.isImageComplete = True
        logging.info(r"Image initialed OK.")

    def rescale_image(self, window: tuple):
        """
        rescale the image to set the data in range (0~255)
        :param window: a tuple pass in as (window width, window center)
        :return: return a np array as rescaled image
        """
        raw_data = self.ImageHU.copy()
        window_upper = window[1] + window[0] / 2
        window_lower = window[1] - window[0] / 2
        # make filter according to center and width
        upper_filter = raw_data > window_upper
        raw_data[upper_filter] = window_upper  # set upper value
        lower_filter = raw_data < window_lower
        raw_data[lower_filter] = window_lower  # set lower value
        # rescale the data to 0~255
        min_hu_image = raw_data.min()
        max_hu_image = raw_data.max()
        if min_hu_image == max_hu_image:
            self.ImageRaw = (raw_data - min_hu_image) * 255
        else:
            # rescale the image to fit 0~255
            self.ImageRaw = (raw_data - min_hu_image) * 255 / (max_hu_image - min_hu_image)

    def calc_circle(self):
        """
        Calculate the image center and radius
        the method is simple
        from up/down/left/right side to go into center
        the 1st number is > mean value, it's the edge
        calculate the distance from th edge to center
        :return: return 2 tuples which are image center and radius 
        (center row, center col),(radius in pixel, radius in cm)
        """
        # set up some local variables
        is_abnormal = False
        center_col = self.Size[0] // 2
        center_row = self.Size[1] // 2
        left_distance = 0
        right_distance = 0
        up_distance = 0
        low_distance = 0
        max_allowed_deviation = 20
        # Using PIL to find edge and convert back to np array
        # This will make calculation more accuracy
        filtered_image = np.array(
            Image.fromarray(self.ImageRaw)
            .convert("L")
            .filter(ImageFilter.FIND_EDGES)
        )

        # start to calculate center col
        for left_distance in range(1, self.Size[1]):
            if filtered_image[center_row, left_distance] != 0:
                break
        for right_distance in range(1, self.Size[1]):
            if filtered_image[center_row, self.Size[1] - right_distance] != 0:
                break
        center_col += (left_distance - right_distance) // 2
        logging.debug(r"Center Col calculated as: " + str(center_col))
        # if the calculated center col deviated too much
        if (self.Size[0] // 2 + max_allowed_deviation) < center_col < (self.Size[0] // 2 - max_allowed_deviation):
            logging.warning(r"It seems abnormal when calculate Center Col, use image center now!")
            center_col = self.Size[0] // 2
            is_abnormal = True

        # start to calculate center row
        for up_distance in range(1, self.Size[0]):
            if filtered_image[up_distance, center_col] != 0:
                break
        for low_distance in range(1, self.Size[0]):
            if filtered_image[self.Size[0] - low_distance, center_col] != 0:
                break
        center_row += (up_distance - low_distance) // 2
        logging.debug(r"Center Row calculated as: " + str(center_row))
        # if the calculated center row deviated too much
        if (self.Size[1] // 2 + max_allowed_deviation) < center_row < (self.Size[1] // 2 - max_allowed_deviation):
            logging.warning(r"It seems abnormal when calculate Center row, use image center now!")
            center_row = self.Size[1] // 2
            is_abnormal = True

        # set different radius according to normal/abnormal situation
        if is_abnormal is False:
            radius = (self.Size[0] - left_distance - right_distance) // 2
            diameter_in_cm = radius * self.PixSpace[0] * 2
            logging.debug(str(radius) + r"pix (radius), " + str(diameter_in_cm) +
                          r"cm(diameter)<==Calculated phantom diameter")
            # standardize the radius
            if diameter_in_cm < 250:
                radius = 233
                logging.debug(str(radius) + r"pix" + r", which is: " +
                              str(radius * self.PixSpace[0] * 2) + r"cm <==Radius Readjusted")
            else:
                radius = 220
                logging.debug(str(radius) + r"pix" + r", which is: " +
                              str(radius * self.PixSpace[0] * 2) + r"cm <==Radius Readjusted")
        else:
            logging.warning(r"Calculated center is abnormal, use 50 as radius!")
            radius = 50
            diameter_in_cm = radius * self.PixSpace[0]

        return (center_row, center_col), (radius, diameter_in_cm)

    def bresenham(self, center, radius):
        """
        Draw circle by bresenham method. And calculate the sum.
        :param center: a tuple to indecate center as (row, col)
        :param radius: set the radius of the calculated circle
        :return: return a tuple as (integration_result, count)
        """
        x = 0
        y = radius
        d = 3 - 2 * radius
        count = 0
        integration_result=0.0
        while x < y:
            integration_result += self.ImageHU[center[0] - y, center[1] + x]
            integration_result += self.ImageHU[center[0] + y, center[1] + x]
            integration_result += self.ImageHU[center[0] - y, center[1] - x]
            integration_result += self.ImageHU[center[0] + y, center[1] - x]
            integration_result += self.ImageHU[center[0] - x, center[1] + y]
            integration_result += self.ImageHU[center[0] - x, center[1] - y]
            integration_result += self.ImageHU[center[0] + x, center[1] + y]
            integration_result += self.ImageHU[center[0] + x, center[1] - y]
            count += 8
            if d < 0:
                d = d + 4 * x + 6
            else:
                d = d + 4 * (x - y) + 10
                y -= 1
            x += 1
        return (integration_result, count)
            
    def roi_measure(self, center, radius):
        result_hu = 0
        result_count = 0
        for index in range(1, radius):
            _result = self.bresenham(center, index)
            result_hu += _result[0]
            result_count += _result[1]
        return(result_hu/result_count)
        
    def find_center_roi_min(self, radius, deviation):
        # initialize local variables
        min=self.roi_measure(self.Center, 10)
        min_row = self.Center[0]
        min_col = self.Center[1]
        # start to find the min HU value
        for index_row in range(self.Center[0]-deviation, self.Center[0]+deviation):
            for index_col in range(self.Center[1]-deviation, self.Center[1]+deviation):
                result=self.roi_measure((index_row, index_col),radius)
                if result < min:
                    min = result
                    min_row = index_row
                    min_col = index_col
        # pack the min value position in image
        min_position=(min_row, min_col)
        return (min, min_position)
                
    def circular_bresenham(self, center, radius, radius_inner):
        x = 0
        y = radius
        d = 3 - 2 * radius
        integration_result = []
        integration_pos = []
        while x < y:
            integration_result.append(self.roi_measure(([center[0] - y, center[1] + x]), radius_inner))
            integration_result.append(self.roi_measure(([center[0] + y, center[1] + x]), radius_inner))
            integration_result.append(self.roi_measure(([center[0] - y, center[1] - x]), radius_inner))
            integration_result.append(self.roi_measure(([center[0] + y, center[1] - x]), radius_inner))
            integration_result.append(self.roi_measure(([center[0] - x, center[1] + y]), radius_inner))
            integration_result.append(self.roi_measure(([center[0] - x, center[1] - y]), radius_inner))
            integration_result.append(self.roi_measure(([center[0] + x, center[1] + y]), radius_inner))
            integration_result.append(self.roi_measure(([center[0] + x, center[1] - y]), radius_inner))
            # record the position to draw afterward
            integration_pos.append(([center[0] - y, center[1] + x]))
            integration_pos.append(([center[0] + y, center[1] + x]))
            integration_pos.append(([center[0] - y, center[1] - x]))
            integration_pos.append(([center[0] + y, center[1] - x]))
            integration_pos.append(([center[0] - x, center[1] + y]))
            integration_pos.append(([center[0] - x, center[1] - y]))
            integration_pos.append(([center[0] + x, center[1] + y]))
            integration_pos.append(([center[0] + x, center[1] - y]))
            if d < 0:
                d = d + 4 * x + 6
            else:
                d = d + 4 * (x - y) + 10
                y -= 1
            x += 1
        return (integration_result, integration_pos)
        
    def evaluate_iq (self, diameter_in_mm, deviation_in_mm):
        if not self.isImageComplete:
                logging.warning(r"Image initialed incomplete. Procedure quited.")
                return
                
        # convert diamter_in_mm into radius in pixel
        radius = int((diameter_in_mm / self.PixSpace[0]) / 2)
        # convert deviation in mm into deviation in pixel
        deviation = int(deviation_in_mm / self.PixSpace[0])
        
        (min_hu, min_pos) = self.find_center_roi_min(radius, deviation)
        (result, pos) = self.circular_bresenham(min_pos, radius*2, radius)
        max_hu = max(result)
        for i in range(0,len(result)):
            result[i] = result[i]-min_hu
            
        max_deviation = max(result)
        max_dev_position = pos[result.index(max_deviation)]
        
        # prepare to save the evaluation result
        image__filename = "_IqEval.jpeg"
        im = Image.fromarray(self.ImageRaw).convert("L")
        pixelMap = im.load()
        draw = ImageDraw.Draw(im)
        # draw the min center positoin
        pixelMap[min_pos[1], min_pos[0]]=0
        pixelMap[min_pos[1]+1, min_pos[0]]=0
        pixelMap[min_pos[1]-1, min_pos[0]]=0
        pixelMap[min_pos[1], min_pos[0]+1]=0
        pixelMap[min_pos[1], min_pos[0]-1]=0
        # draw the max deviation center position
        pixelMap[max_dev_position[1], max_dev_position[0]]=0
        pixelMap[max_dev_position[1]+1, max_dev_position[0]]=0
        pixelMap[max_dev_position[1]-1, max_dev_position[0]]=0
        pixelMap[max_dev_position[1], max_dev_position[0]+1]=0
        pixelMap[max_dev_position[1], max_dev_position[0]-1]=0
        # draw the Image Center Position
        pixelMap[self.Center[1], self.Center[0]]=0
        pixelMap[self.Center[1]+1, self.Center[0]]=0
        pixelMap[self.Center[1]-1, self.Center[0]]=0
        pixelMap[self.Center[1], self.Center[0]+1]=0
        pixelMap[self.Center[1], self.Center[0]-1]=0
        # Draw circle
        text_pos = deviation
        draw.ellipse((min_pos[1]-radius, min_pos[0]-radius, min_pos[1]+radius, min_pos[0]+radius))
        draw.text((min_pos[1], min_pos[0]+text_pos), str("Middle Min HU:"+str(min_hu)))
        draw.ellipse((max_dev_position[1]-radius, max_dev_position[0]-radius, max_dev_position[1]+radius, max_dev_position[0]+radius))
        draw.text((max_dev_position[1], max_dev_position[0]+text_pos), str("Around Max HU:"+str(max_hu)))
        draw.text((200, 100), str("Max HU Deviation:"+str(max_deviation)))
        im.save(self.FileName + "_" + self.ScanMode + image__filename, "png")
        
        # Prepare to draw the image evaluation fig plot
        image__filename__fig = "_IqEval_fig.jpeg"
        plt.plot(sorted(result))
        limit_h = []
        limit_l = []
        limit_h1 = []
        limit_l1 = []
        for i in result:
            limit_h.append(3)
            limit_h1.append(3.5)
            limit_l.append(-3)
            limit_l1.append(-3.5)
        plt.plot(limit_h)
        plt.plot(limit_l)
        plt.plot(limit_h1)
        plt.plot(limit_l1)
        plt.savefig(self.FileName + "_" + self.ScanMode + image__filename__fig)
        plt.close()
        
                
    def integration(self):
        # calculate circular integration for each radius
        for index in range(1, len(self.Image_Integration_Result)):
            result = self.bresenham(self.Center, index)
            self.Image_Integration_Result[index] = result[0]/result[1]
        # calculate data by using Median
        # for the rest of the data, do the median filter with width
        _width = 8
        for index in range(len(self.Image_Integration_Result) - _width):
            self.Image_Median_Filter_Result[index] = np.median(
                self.Image_Integration_Result[index:index + _width])

    def save_image(self):
        if not self.isImageComplete:
            logging.warning(r"Image initialed incomplete. Procedure quited.")
            return
        # set up the output file name
        image__filename = ".jpeg"
        image__filename__fig = "_fig.jpeg"
        im = Image.fromarray(self.ImageRaw).convert("L")
        # save image
        try:
            # save image
            im.save(self.FileName + "_" + self.ScanMode + image__filename, "png")
            # draw fig
            plt.plot(self.Image_Median_Filter_Result)
            plt.ylim((-5, 20))
            plt.xlim((0, 250))
            # draw fig image
            plt.savefig(self.FileName + "_" + self.ScanMode + image__filename__fig)
            plt.close()
        except Exception as e:
            logging.error(str(e))
            return
        finally:
            plt.close()

    def show_image(self):
        if not self.isImageComplete:
            logging.warning(r"Image initialed incomplete. Procedure quited.")
            return
        return Image.fromarray(self.ImageRaw).convert("L")

    def show_integration_result(self):
        if not self.isImageComplete:
            logging.warning(r"Image initialed incomplete. Procedure quited.")
            return
        return self.Image_Median_Filter_Result


if __name__ == '__main__':
    print("please do not use it individually unless of debugging.")

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                        datefmt='%a, %d %b %Y %H:%M:%S')

    img = ImageHandler('a.dcm')
    img.rescale_image((2, 100))
    img.save_image()
