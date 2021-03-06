import cv2
import numpy as np
import math
from imgUtils import ColorMask as colMaks


class YasnoffMoments:


    def __init__(self, template, img):


        # пространственные моменты
        self._used_moments = ['m00', 'm10', 'm01', 'm20', 'm11', 'm02', 'm30', 'm21', 'm12', 'm03']

        # центральные моменты
        # self._used_moments = ['mu20', 'mu11', 'mu02', 'mu30', 'mu21', 'mu12', 'mu03']

        # n
        # self._used_moments = ['nu11', 'nu20', 'nu12', 'nu02', 'nu21', 'nu03', 'nu30']

        # all
        # self._used_moments = ['m20', 'mu02', 'mu30', 'm02', 'mu20', 'm03', 'mu12', 'm11', 'nu11', 'nu20',
        #                       'mu03', 'nu12', 'm01', 'm21', 'm30', 'm00', 'm10', 'nu02', 'mu21', 'nu21',
        #                       'nu03', 'nu30', 'mu11', 'm12']

        # # наиболее "удачная" подборка
        # self._used_moments = ['m00', 'm10', 'm12', 'mu12']



        self._template = template
        self._img = img

        self._height = img.shape[0]
        self._width = img.shape[1]

        templObjs = colMaks.getMaskFromColors(template)
        segmObjs = colMaks.getMaskFromColors(img)

        self._templ_len = len(templObjs)
        self._segm_len = len(segmObjs)

        sortTemplObjs = self._sortBySize(templObjs)
        sortSegmObjs = self._sortByBitwise(sortTemplObjs, segmObjs)

        self._confMatrix = self._createDiffMatrix(sortTemplObjs, sortSegmObjs)
        self._contMomentMatrix = self._createMommentsMatrix(sortTemplObjs, sortSegmObjs)


    def _sortBySize(self, templObjs):
        # сортируем массив с шаблонами по размеру найденных элементов
        def sortBySize(img):
            count = cv2.countNonZero(img)
            return 0 - count  # для сортировки по убыванию

        templObjs.sort(key=sortBySize)
        return templObjs


    def _sortByBitwise(self, templObjs, segmObjs):
        templ_len = self._templ_len
        segm_len = self._segm_len

        diff_matrix = self._createDiffMatrix(templObjs, segmObjs)

        # получаем по порядку индексы элементов, имеющих минимальную разницу с шаблонами
        row_indexes = []
        for cell_idx in range(0, templ_len):  # переменная индекса столбца
            max_row_val = -1
            max_row_idx = -1

            for j in range(0, segm_len):
                row = diff_matrix[j]
                val = row[cell_idx]

                if val > max_row_val and j not in row_indexes:
                    max_row_val = val
                    max_row_idx = j

            if max_row_idx != -1:
                row_indexes.append(max_row_idx)

        # добавляем по порядку все найденные соотвесвующие объекты
        sorted_segmObjs = []
        for idx in row_indexes:
            sorted_segmObjs.append(segmObjs[idx])

        # добавляем все оставшиеся объекты
        for i in range(0, len(segmObjs)):
            if i not in row_indexes:
                sorted_segmObjs.append(segmObjs[i])

        return sorted_segmObjs


    def _createDiffMatrix(self, templObjs, segmObjs):

        # заполняем двумерный массив пиксельной разницей
        max_length = max(len(segmObjs), len(templObjs))
        diff_matrix = np.zeros((max_length, max_length))

        for i in range(0, len(segmObjs)):
            segm = segmObjs[i]

            if segm.ndim == 3:  # если изображение не одноканальное
                segm = cv2.cvtColor(segm, cv2.COLOR_BGR2GRAY)  # преобразуем в оттенки серого

            for j in range(0, len(templObjs)):
                templ = templObjs[j]
                intersec = cv2.bitwise_and(templ, segm)
                ptCount = cv2.countNonZero(intersec)
                diff_matrix[i][j] = ptCount

        return diff_matrix


    def _createMommentsMatrix(self, templObjs, segmObjs):
        img_height = self._height
        img_width = self._width

        temp_len = len(templObjs)
        segm_len = len(segmObjs)

        # расчитываем моменты
        temp_moments = self._getMomentsFromArray(templObjs)
        segm_moments = self._getMomentsFromArray(segmObjs)

        max_length = max(temp_len, segm_len)
        contMomentMatrix = np.zeros((max_length, max_length))

        # расчитываем разницу моментов
        for i in range(0, temp_len):
            temp_moment = temp_moments[i]

            for j in range(0, segm_len):
                segm_moment = segm_moments[j]
                moments_diff = self._get_moments_diff(temp_moment, segm_moment)
                contMomentMatrix[j][i] = moments_diff

                # if i == 3 and j == 3:
                #     # print('temp_moment = {0}'.format(temp_moment))
                #     # print('segm_moment = {0}'.format(segm_moment))
                #     print('moments_diff = {0}'.format(moments_diff))
                #
                #
                #     print(' -- template moments -- ')
                #     tt_mom = self._getMoments_test(templObjs[3])
                #
                #     print(' -- segm moments -- ')
                #     to_mom = self._getMoments_test(segmObjs[3])
                #
                #     t_diff = self._get_moments_diff_test(tt_mom, to_mom)
                #     print('moments_diff = {0}'.format(moments_diff))
                #     print('t_diff = {0}'.format(t_diff))
                #
                #     print('------------------------')
                #
                #     cv2.imshow("templObj", templObjs[3])
                #     cv2.imshow("segmObj", segmObjs[3])
                #     cv2.waitKey()


        # можно не использовать потому что разница между любым объектом и одним пикселем стремится к 1
        # ------

        if temp_len > segm_len:
            blank_image = np.zeros([img_height, img_width, 3], dtype=np.uint8)
            cnt_y = img_width // 2
            cnt_x = img_height // 2
            blank_image[cnt_x, cnt_y] = (255, 255, 255)
            blank_image = cv2.cvtColor(blank_image, cv2.COLOR_BGR2GRAY)
            blank_moment = self._getMoments(blank_image)

            for i in range(segm_len, temp_len):
                temp_moment = temp_moments[i]
                moments_diff = self._get_moments_diff(blank_moment, temp_moment)
                contMomentMatrix[i][i] = moments_diff

        # ------

        # # -- test --
        # templObjs[3]
        # segmObjs[3]

        return contMomentMatrix


    def _get_moments_diff(self, moment1, moment2, base = 4):
        diff_moments = []
        for m_key in self._used_moments:
            obj_m = moment1[m_key]
            temp_m = moment2[m_key]

            max_m = max(obj_m, temp_m)
            min_m = min(obj_m, temp_m)

            if max_m != 0:
                # # diff = abs((1 / temp_m) - (1 / obj_m))  # CV_CONTOURS_MATCH_I1
                # # diff = abs(temp_m - obj_m)              # CV_CONTOURS_MATCH_I2
                diff = abs((max_m - min_m) / max_m)         # CV_CONTOURS_MATCH_I3
                diff_moments.append(diff)
            else:
                diff_moments.append(0)

        contour_diff = sum(diff_moments) / len(diff_moments)
        result = contour_diff ** (1 / base)
        return result


    def _getMoments(self, img):
        if img.ndim == 3:  # если изображение не одноканальное
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # преобразуем в оттенки серого

        _, contours, _ = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        moment = {'mu21': 0.0, 'nu20': 0.0, 'm30': 0.0, 'nu11': 0.0, 'm02': 0.0, 'nu03': 0.0, 'm20': 0.0,
                  'm11': 0.0, 'mu02': 0.0, 'mu20': 0.0, 'nu21': 0.0, 'nu12': 0.0, 'nu30': 0.0, 'm10': 0.0,
                  'm03': 0.0, 'mu11': 0.0, 'mu03': 0.0, 'mu12': 0.0, 'm01': 0.0, 'mu30': 0.0, 'm12': 0.0,
                  'm00': 0.0, 'm21': 0.0, 'nu02': 0.0}

        for cnt in contours:
            m = cv2.moments(cnt)
            for key in moment.keys():
                moment[key] = moment[key] + m[key]
        return moment


    def _getMomentsFromArray(self, images):
        # проходим по всем сегментированным объектам и считаем моменты
        moments = []
        for img in images:
            m = self._getMoments(img)
            moments.append(m)
        return (moments)




    def _getIncorrectlyClassifiedPixels(self, confMatrix):
        height = self._segm_len
        width = self._templ_len

        result = []
        for i in range(0, len(confMatrix)):

            # правильно класифицированные пиксели
            c_kk = 0
            if i < width and i < height:
                c_kk = confMatrix[i][i]

            # сумма всех пикселей полученого шаблона
            c_ik = 0
            for row in confMatrix:
                if i < len(row):
                    val = row[i]
                    c_ik = c_ik + val

            # расчет значения
            if c_ik != 0:
                res_val = ((c_ik - c_kk) / c_ik) * 100
                result.append(res_val)
            else:
                result.append(0)

        return result


    def _getWronglyAssignedToClass(self, confMatrix):
        height = self._segm_len
        width = self._templ_len

        result = []
        for i in range(0, len(confMatrix)):

            # правильно класифицированные пиксели
            c_kk = 0
            if i < width and i < height:
                c_kk = confMatrix[i][i]

            # сумма всех пикселей полученого шаблона
            c_ik = 0
            for row in confMatrix:
                if i < len(row):
                    val = row[i]
                    c_ik = c_ik + val

            # сумма всех пикселей полученого объекта
            c_ki = 0
            if i < height:
                row = confMatrix[i]
                for val in row:
                    c_ki = c_ki + val

            # общая сумма
            total = 0
            for row in confMatrix:
                total = total + sum(row)

            # расчет значения
            res_val = ((c_ki - c_kk) / (total - c_ik)) * 100
            result.append(res_val)

        return result



    def printMatrix(self):
        contMomentMatrix = self._contMomentMatrix
        confMatrix = self._confMatrix

        # получаем количество шаблонов и объектов
        height = self._segm_len
        width = self._templ_len

        row_names = []
        for i in range(0, height):
            row_names.append('Object %s' % i)

        cell_names = []
        for i in range(0, width):
            cell_names.append('Object %s' % i)

        # Создаем архивы для хранения имен столбцов и колонок
        rows_names = []
        for i in range(0, height):
            rows_names.append('Object %s' % i)

        cell_names = []
        for i in range(0, width):
            cell_names.append('Template %s' % i)

        # Печать значений
        row_format = "{:>22}" * (width + 1)
        print(row_format.format("", *cell_names))

        for name, conf_row, mom_row in zip(row_names, confMatrix, contMomentMatrix):
            str_row = []
            for idx in range(0, len(conf_row)):
                cell = conf_row[idx]
                moment = round(mom_row[idx], 4)
                moment_str = '{:>8}'.format(moment)
                val = '{0} : {1}'.format(cell, moment_str)
                str_row.append(val)
            print(row_format.format(name, *str_row))


    def printMatrixWithTotal(self):
        confMatrix = self._confMatrix

        # получаем количество шаблонов и объектов
        height = self._segm_len
        width = self._templ_len

        # создание и расчет массивов с суммами
        rowTotals = [0] * (height + 1)
        cellTotals = [0] * (width + 1)

        rowIndex = 0
        for i in range(0, height):
            row = confMatrix[i]
            cellTotal = 0
            cellIndex = 0

            for j in range(0, width):
                cell = row[j]
                cellTotal = cellTotal + cell
                cellTotals[cellIndex] = cellTotals[cellIndex] + cell
                cellIndex = cellIndex + 1

            rowTotals[rowIndex] = cellTotal
            rowIndex = rowIndex + 1

        row_names = []
        for i in range(0, height):
            row_names.append('Object %s' % i)

        cell_names = []
        for i in range(0, width):
            cell_names.append('Object %s' % i)

        row_names.append('Total')
        cell_names.append('Total')

        # создание новой матрицы с Total
        resultMatrix = np.zeros((height + 1, width + 1))

        # Наполнение значенями из сторой матрицы
        rowIndex = 0
        for i in range(0, height):
            row = confMatrix[i]
            cellIndex = 0

            for j in range(0, width):
                cell = row[j]
                resultMatrix[rowIndex, cellIndex] = cell
                cellIndex = cellIndex + 1
            rowIndex = rowIndex + 1

        # Добавление сумм
        for j in range(0, height):
            resultMatrix[j][width] = rowTotals[j]

        for i in range(0, width):
            resultMatrix[height][i] = cellTotals[i]

        resultMatrix[height][width] = sum(cellTotals)

        # Создаем архивы для хранения имен столбцов и колонок
        rows_names = []
        for i in range(0, height):
            rows_names.append('Object %s' % i)

        cell_names = []
        for i in range(0, width):
            cell_names.append('Temaple %s' % i)

        row_names.append('Total')
        cell_names.append('Total')

        # Печать значений
        row_format = "{:>15}" * (width + 2)
        print(row_format.format("", *cell_names))

        for name, row in zip(row_names, resultMatrix):
            print(row_format.format(name, *row))


    def getIncorrecClassPixels(self):
        confMatrix = self._confMatrix
        m1 = self._getIncorrectlyClassifiedPixels(confMatrix)

        result = sum(m1) / len(m1)
        return result


    def getWronglyAssigneToClass(self):
        confMatrix = self._confMatrix
        m2 = self._getWronglyAssignedToClass(confMatrix)

        result = sum(m2)
        return result


    def getFrags(self, a=0.16, b=2):
        templ_len = self._templ_len
        segm_len = self._segm_len

        frag = 1 / 1 + (a * math.fabs((segm_len - templ_len)) ** b)
        return frag


    def get_m3(self):
        height = self._segm_len
        width = self._templ_len
        contMomentMatrix = self._contMomentMatrix

        min_l = min(height, width)

        result = []
        for i in range(0, min_l):
            i_kk = contMomentMatrix[i][i]
            result.append(i_kk)
            if i == 3:
                print('i = {0}'.format(i))
                print('i_kk = {0}'.format(i_kk))
                print('-------------------')

        # показатель даже при минимальном отклонении стремится к 1-це
        # поэтому для простоты можно просто ставить единицу
        '''
        for i in range(height, width):
            result.append(1)
        '''
        # -------
        # для более точных расчетов
        for i in range(height, width):
            val = contMomentMatrix[i][i]
            result.append(val)
        # -------

        print('result = {0}'.format(result))

        return sum(result) / len(result)


    def get_m4(self):
        height = self._segm_len
        width = self._templ_len
        contMomentMatrix = self._contMomentMatrix
        length = width #len(contMomentMatrix)
        result = []


        for i in range (0, length):

            # то что лежит на диагонали
            m_kk = contMomentMatrix[i][i]

            m_ik = 0
            for row in contMomentMatrix:
                val = row[i]
                m_ik = m_ik + val

            m_ki = 0
            row = contMomentMatrix[i]
            for val in row:
                m_ki = m_ki + val

            # общая сумма
            total = 0
            for row in contMomentMatrix:
                total = total + sum(row)

        #     print('m_kk - {0}'.format(m_kk))
        #     print('m_ik - {0}'.format(m_ik))
        #     print('m_ki - {0}'.format(m_ki))
        #     print('-------------------------')
        #
        # print('height = {0}'.format(height))
        # print('width = {0}'.format(width))
        # print('len(contMomentMatrix) = {0}'.format(len(contMomentMatrix)))

        res_val = ((m_ki - m_kk) / (total - m_ik))
        result.append(res_val)

        return sum(result)

    # ------------
    # --- test ---
    # ------------
    def _get_moments_diff_test(self, moment1, moment2, base = 4):
        diff_moments = []
        for m_key in self._used_moments:
            obj_m = moment1[m_key]
            temp_m = moment2[m_key]

            max_m = max(obj_m, temp_m)
            min_m = min(obj_m, temp_m)

            if max_m != 0:
                # # diff = abs((1 / temp_m) - (1 / obj_m))  # CV_CONTOURS_MATCH_I1
                # # diff = abs(temp_m - obj_m)              # CV_CONTOURS_MATCH_I2
                diff = abs((max_m - min_m) / max_m)         # CV_CONTOURS_MATCH_I3
                diff_moments.append(diff)
            else:
                diff_moments.append(0)

        contour_diff = sum(diff_moments) / len(diff_moments)
        result = contour_diff ** (1 / base)
        return result


    def _getMoments_test(self, img):
        if img.ndim == 3:  # если изображение не одноканальное
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # преобразуем в оттенки серого

        _, contours, _ = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        moment = {'mu21': 0.0, 'nu20': 0.0, 'm30': 0.0, 'nu11': 0.0, 'm02': 0.0, 'nu03': 0.0, 'm20': 0.0,
                  'm11': 0.0, 'mu02': 0.0, 'mu20': 0.0, 'nu21': 0.0, 'nu12': 0.0, 'nu30': 0.0, 'm10': 0.0,
                  'm03': 0.0, 'mu11': 0.0, 'mu03': 0.0, 'mu12': 0.0, 'm01': 0.0, 'mu30': 0.0, 'm12': 0.0,
                  'm00': 0.0, 'm21': 0.0, 'nu02': 0.0}

        for cnt in contours:
            m = cv2.moments(cnt)
            for key in moment.keys():
                moment[key] = moment[key] + m[key]

            # test_m = {}
            # for key in self._used_moments:
            #     test_m.update([(key,  moment[key])])
            #
            # print('1moment = {0}'.format(test_m))
            # img_height = self._height
            # img_width = self._width
            # cnt_image = np.zeros([img_height, img_width, 3], dtype=np.uint8)
            # cv2.drawContours(cnt_image, cnt, -1, (0, 255, 0), 1)
            # cv2.imshow("cnt", cnt_image)
            # cv2.waitKey()

        return moment