from UserException import InvalidDatasetException
import numpy as np
from sklearn.model_selection import train_test_split
import pandas as pd

class DataPreprocessing():

    oldLabels=None
    newLabels = None
    mergedLabelDF = None
    attribute_doc_df = None

    def __init__(self):
        pass

    def generateValidationSet(self,trainset, test_size=0.2):
        """
        Changelog:
        - 14/3 KS First Commit
        Split the training set into train and validation sets.
        :param trainset:
        :param test_size: Default test size is 20% of original data
        :return:
        """
        print("Creating validation set")
        print("trainset shape:",trainset.shape)
        train,validation=train_test_split(trainset,test_size=test_size,random_state=42)
        print("splitted trainset shape:", train.shape)
        print("splitted validation shape:", validation.shape)
        return train,validation

    def __replaceLabel(self,x):
        """
        Changelog:
        - 14/3 KS First Commit
        Look up old labels and map to new labels
        :param x:
        :return:
        """
        indexRow=np.where(self.oldLabels == x)
        newLabel=self.newLabels[indexRow][0]
        return newLabel

    def transformLabels(self,trainDF=None, validationDF=None, trainLabelColumn='relevance', validationLabelColumn='relevance', newColName="relevance_int"):
        """
        Changelog:
        - 14/3 KS First Commit
        Existing labels are real numbers. This method will transform them into
         discrete numbers in the respective ordering starting from 0.
         Only run this method if your model requires labels to be discrete and ordered integers.

        :param trainDF: Required. Dataframe of training set
        :param validationDF: Optional. Datatframe of validation set
        :param newColName: Optional. This will be the name of the new column appended to both trainDF and testDF
        :param trainLabelColumn: Optional. Column of the label in the training set
        :param validationLabelColumn: Optional. Column of the label in the validation set

        :return:
        """

        # if(trainDF==None or validationDF==None):
        #     raise InvalidDatasetException("Invalid datasets","Both train and validation datasets must be provided ")
        print("===========Tranforming labels...\nshowing current values")


        if(trainDF is not None and validationDF is not None):
            print("trainDF:", list(trainDF))
            print("trainDF:", trainDF.head(1))
            print("validationDF:", list(validationDF))
            print("validationDF:", validationDF.head(1))

            #merge train and validation dataframe
            trainLabelDF=pd.DataFrame(trainDF[trainLabelColumn])
            print("Extracted trainLabelDF:",list(trainLabelDF),"\n",type(trainLabelDF),trainLabelDF.shape,trainLabelDF.head(1))
            trainLabelDF.columns=[trainLabelColumn]
            validationLabelDF = pd.DataFrame(validationDF[validationLabelColumn])
            print("Extracted validationLabelDF:", list(validationLabelDF), "\n", type(validationLabelDF),validationLabelDF.shape, validationLabelDF.head(1))
            validationLabelDF.columns = [trainLabelColumn]
            self.mergedLabelDF=trainLabelDF.append(validationLabelDF)
        elif(trainDF is not None and validationDF is None):
            print("trainDF:", list(trainDF))
            print("trainDF:", trainDF.head(1))

            self.mergedLabelDF=pd.DataFrame(trainDF[trainLabelColumn])
        else:
            raise InvalidDatasetException("Invalid dataset","The training set must exists")

        print("self.mergedLabelDF:", list(self.mergedLabelDF), "\n", type(self.mergedLabelDF), self.mergedLabelDF.shape, self.mergedLabelDF.head(1))

        #Get existing unique labels
        self.oldLabels = self.mergedLabelDF[trainLabelColumn].sort_values().unique()
        print("Old unique Labels:",self.oldLabels)

        #Generate new labels
        self.newLabels = np.arange(0, self.mergedLabelDF[trainLabelColumn].sort_values().unique().shape[0])
        print('newLabels:',self.newLabels)

        #Label replacement
        print("Creating new column for training: ",newColName)
        trainDF[newColName] = trainDF[trainLabelColumn].map(self.__replaceLabel)
        if (validationDF is not None):
            print("Creating new column for validation: ",newColName)
            validationDF[newColName] = validationDF[validationLabelColumn].map(self.__replaceLabel)
        print("===========Transform labels completed")


        if (validationDF is None):
            return trainDF
        else:
            return trainDF, validationDF


    def getBagOfWords(self, documentDF=None, return_type='document_tokens'):
        """
        To retrieve a bag of words from the documents (No pre-processing except tokenisation)
        changelog
        - 15/3 KS First commit
        :param documentDF: Strictly a Nx1 Dataframe. Row representing document, Col representing a string of words
        :param return_type: 'document_tokens' returns a NxM array (Sparse), each row representing a document, each col representing a token of the document.
                            'array_tokens' returns a Nx1 array, each row representing a token
        :return:
        """

        texts=[]
        if(return_type=='document_tokens'):
            print("Document level tokenisation")
            texts=[words for words in (document.lower().split() for document in documentDF)]
        elif(return_type=='array_tokens'):
            print("Highest level tokenisation")
            for words in (document.lower().split() for document in documentDF):
                for word in words:
                    texts.append(word)
        return texts

    def getAttributeDoc(self, attribute_df):
        """
        Produce concatenated attributes for a product in json format flattened/unnflattened.
        This can then be vectorised e.g using doc2vec.
        :param attribute_df: attribute_df as read in using HomeDepotReader
        :return: pd dataframe with 'product_uid','attr_json' columns where 'attr_json' is flattened json of all attributes
        """
        # skip nan row e.g Pandas(Index=1929, product_uid=nan, name=nan, value=nan)
        tmp_attribute_df = attribute_df.copy()
        tmp_attribute_df['product_uid'].replace('', np.nan,
                                                inplace=True)  # replace any blanks with NaN so we can drop it next
        tmp_attribute_df.dropna(subset=['product_uid'], inplace=True)  # drop null values

        # TODO: should Bullet01 e.g be modified as it doesn't add value per se
        # TODO: could also only keep 'important' attributes
        new_rows_list = []
        current_product_uid = None
        for row in tmp_attribute_df.itertuples():  # itertuples over iterrows for speed as doesn't cast to pd.series
            product_uid = row.product_uid
            if product_uid != current_product_uid:
                # new product,
                # store prev json into df
                if current_product_uid != None:
                    new_rows_list.append(attr_dict)
                # start new dict
                current_product_uid = product_uid
                attr_dict = {}
                attr_dict['product_uid'] = product_uid
                attr_dict['attr_json'] = {row.name: row.value}

            else:
                # existing product, continue prev dict
                attr_dict['attr_json'].update({row.name: row.value})

        attribute_doc_df = pd.DataFrame(new_rows_list, columns=['product_uid', 'attr_json'])
        attribute_doc_df['product_uid'] = attribute_doc_df['product_uid'].astype(int)
        return attribute_doc_df

#Test for getAttributeDoc
# if __name__ == "__main__":
#     attribute_filename = '../data/attributes.csv'
#     attribute_df = pd.read_csv(attribute_filename, delimiter=',', low_memory=False)#, encoding="ISO-8859-1")
#     dp = DataPreprocessing()
#     attribute_doc_df = dp.getAttributeDoc(attribute_df)
#     print(len(attribute_doc_df))
#     print(len(attribute_df))
#     print(attribute_doc_df.head(10))
#     print(attribute_doc_df.iloc[0][1])

