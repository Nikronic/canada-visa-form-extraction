__all__ = [
    "DataframePreprocessor",
    "CanadaDataframePreprocessor",
    "FileTransformCompose",
    "FileTransform",
    "CopyFile",
    "MakeContentCopyProtectedMachineReadable",
]

import logging
import shutil
from typing import Any, Callable, Optional

import numpy as np
import pandas as pd
import pikepdf
from dateutil import parser
from dateutil.relativedelta import *

from cvfe.configs import CANADA_COUNTRY_CODE_TO_NAME
from cvfe.data import functional
from cvfe.data.constant import *
from cvfe.data.pdf import CanadaXFA

# config logger
logger = logging.getLogger(__name__)


class DataframePreprocessor:
    """A wrapper around builtin Pandas functions to make it easier for our data values

    A class that contains methods for dealing with dataframes regarding
    transformation of data such as filling missing values, dropping columns,
    or aggregating multiple columns into a single more meaningful one.

    This class needs to be extended for file specific preprocessing where tags are
    unique and need to be done entirely manually.
    In this case, :func:`file_specific_basic_transform` needs to be implemented.
    """

    def __init__(self, dataframe: pd.DataFrame = None) -> None:
        """

        Args:
            dataframe (:class:`pandas.DataFrame`, optional): Main dataframe to be preprocessed.
                Defaults to None.
        """
        self.dataframe = dataframe

    def column_dropper(
        self,
        string: str,
        exclude: Optional[str] = None,
        regex: bool = False,
        inplace: bool = True,
    ) -> Optional[pd.DataFrame]:
        """See :func:`cvfe.data.functional.column_dropper` for more information"""

        return functional.column_dropper(
            dataframe=self.dataframe,
            string=string,
            exclude=exclude,
            regex=regex,
            inplace=inplace,
        )

    def fillna_datetime(
        self,
        col_base_name: str,
        type: DocTypes,
        one_sided: str | bool,
        date: Optional[str] = None,
        inplace: bool = False,
    ) -> Optional[pd.DataFrame]:
        """See :func:`cvfe.data.functional.fillna_datetime` for more details"""
        if date is None:
            date = T0

        return functional.fillna_datetime(
            dataframe=self.dataframe,
            col_base_name=col_base_name,
            one_sided=one_sided,
            date=date,
            inplace=inplace,
            type=type,
        )

    def aggregate_datetime(
        self,
        col_base_name: str,
        new_col_name: str,
        type: DocTypes,
        if_nan: Optional[str | Callable] = None,
        one_sided: Optional[str] = None,
        reference_date: Optional[str] = None,
        current_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """See :func:`cvfe.data.functional.aggregate_datetime` for more details"""
        return functional.aggregate_datetime(
            dataframe=self.dataframe,
            col_base_name=col_base_name,
            new_col_name=new_col_name,
            one_sided=one_sided,
            if_nan=if_nan,
            type=type,
            reference_date=reference_date,
            current_date=current_date,
        )

    def file_specific_basic_transform(self, type: DocTypes, path: str) -> pd.DataFrame:
        """
        Takes a specific file then does data type fixing, missing value filling, discretization, etc.

        Note:
            Since each files has its own unique tags and requirements,
            it is expected that all these transformation being hardcoded for each file,
            hence this method exists to just improve readability without any generalization
            to other problems or even files.

        Args:
            type (DocTypes): The input document type (see :class:`DocTypes <cvfe.data.constant.DocTypes>`)
            path (str): Path to the input document
        """

        raise NotImplementedError

    def change_dtype(
        self,
        col_name: str,
        dtype: Callable,
        if_nan: str | Callable = "skip",
        **kwargs,
    ):
        """See :func:`cvfe.data.functional.change_dtype` for more details"""

        return functional.change_dtype(
            dataframe=self.dataframe,
            col_name=col_name,
            dtype=dtype,
            if_nan=if_nan,
            **kwargs,
        )

    def config_csv_to_dict(self, path: str) -> dict:
        """
        Take a config CSV and return a dictionary of key and values

        Args:
            path (str): string path to config file
        """

        config_df = pd.read_csv(path)
        return dict(
            zip(config_df[config_df.columns[0]], config_df[config_df.columns[1]])
        )


class CanadaDataframePreprocessor(DataframePreprocessor):
    def __init__(self, dataframe: Optional[pd.DataFrame] = None) -> None:
        super().__init__(dataframe)
        self.base_date = (
            None  # the time forms were filled, considered "today" for forms
        )

        # get country code to name dict
        self.config_path = CANADA_COUNTRY_CODE_TO_NAME
        self.CANADA_COUNTRY_CODE_TO_NAME = self.config_csv_to_dict(self.config_path)

    def convert_country_code_to_name(self, string: str) -> str:
        """
        Converts the (custom and non-standard) code of a country to its name given the XFA docs LOV section.

        Args:
            string (str): input code string
        """

        country = [c for c in self.CANADA_COUNTRY_CODE_TO_NAME.keys() if string in c]
        if country:
            return self.CANADA_COUNTRY_CODE_TO_NAME[country]
        else:
            logger.debug(
                (
                    f'"{string}" country code could not be found'
                    f'in the config file="{self.config_path}".'
                )
            )
            return CanadaFillna.COUNTRY_CODE_5257E

    def file_specific_basic_transform(self, type: DocTypes, path: str) -> pd.DataFrame:
        canada_xfa = CanadaXFA()  # Canada PDF to XML

        if type == DocTypes.CANADA_5257E:
            # XFA to XML
            xml = canada_xfa.extract_raw_content(path)
            xml = canada_xfa.clean_xml_for_csv(xml=xml, type=DocTypes.CANADA_5257E)
            # XML to flattened dict
            data_dict = canada_xfa.xml_to_flattened_dict(xml=xml)
            data_dict = canada_xfa.flatten_dict(data_dict)
            # clean flattened dict
            data_dict = functional.dict_summarizer(
                data_dict,
                cutoff_term=CanadaCutoffTerms.CA5257E,
                KEY_ABBREVIATION_DICT=CANADA_5257E_KEY_ABBREVIATION,
                VALUE_ABBREVIATION_DICT=CANADA_5257E_VALUE_ABBREVIATION,
            )
            # convert each data dict to a dataframe
            dataframe = pd.DataFrame.from_dict(data=[data_dict], orient="columns")
            self.dataframe = dataframe
            # drop pepeg columns
            #   warning: setting `errors='ignore` ignores errors if columns do not exist!
            dataframe.drop(
                CANADA_5257E_DROP_COLUMNS, axis=1, inplace=True, errors="ignore"
            )

            # Adult binary state: adult=True or child=False
            dataframe["P1.AdultFlag"] = dataframe["P1.AdultFlag"].apply(
                lambda x: True if x == "adult" else False
            )
            # service language: 1=En, 2=Fr -> need to be changed to categorical
            dataframe = self.change_dtype(
                col_name="P1.PD.ServiceIn.ServiceIn", dtype=np.int8, if_nan="skip"
            )
            # AliasNameIndicator: 1=True, 0=False
            dataframe[
                "P1.PD.AliasName.AliasNameIndicator.AliasNameIndicator"
            ] = dataframe[
                "P1.PD.AliasName.AliasNameIndicator.AliasNameIndicator"
            ].apply(
                lambda x: True if x == "Y" else False
            )
            # VisaType: String -> categorical
            dataframe = self.change_dtype(
                col_name="P1.PD.VisaType.VisaType",
                dtype=str,
                if_nan="fill",
                value=CanadaFillna.VISA_TYPE_5257E,
            )
            # Birth City: String -> categorical
            dataframe = self.change_dtype(
                col_name="P1.PD.PlaceBirthCity",
                dtype=str,
                if_nan="fill",
                value=CanadaFillna.PLACE_BIRTH_CITY_5257E,
            )
            # Birth country: string -> categorical
            dataframe = self.change_dtype(
                col_name="P1.PD.PlaceBirthCountry",
                dtype=str,
                if_nan="fill",
                value=CanadaFillna.COUNTRY_5257E,
            )
            # citizen of: string -> categorical
            dataframe = self.change_dtype(
                col_name="P1.PD.Citizenship.Citizenship",
                dtype=str,
                if_nan="fill",
                value=CanadaFillna.CITIZENSHIP_5257E,
            )
            # current country of residency: string -> categorical
            dataframe = self.change_dtype(
                col_name="P1.PD.CurrCOR.Row2.Country",
                dtype=str,
                if_nan="fill",
                value=CanadaFillna.COUNTRY_5257E,
            )
            # current country of residency status: string -> categorical
            dataframe = self.change_dtype(
                col_name="P1.PD.CurrCOR.Row2.Status",
                dtype=np.int8,
                if_nan="fill",
                value=np.int8(CanadaFillna.RESIDENCY_STATUS_5257E),
            )
            # current country of residency other description: bool -> categorical
            dataframe = self.change_dtype(
                col_name="P1.PD.CurrCOR.Row2.Other",
                dtype=bool,
                if_nan="fill",
                value=CanadaFillna.OTHER_DESCRIPTION_INDICATOR_5257E,
            )
            # validation date of information, i.e. current date: datetime
            dataframe = self.change_dtype(
                col_name="P3.Sign.C1CertificateIssueDate",
                dtype=parser.parse,
                if_nan="skip",
            )
            # keep it so we can access for other file if that was None
            if not dataframe["P3.Sign.C1CertificateIssueDate"].isna().all():
                self.base_date = dataframe["P3.Sign.C1CertificateIssueDate"]
            # date of birth in year: string -> datetime
            dataframe = self.change_dtype(
                col_name="P1.PD.DOBYear", dtype=parser.parse, if_nan="skip"
            )
            # current country of residency period: None -> Datetime (=age period)
            dataframe = self.change_dtype(
                col_name="P1.PD.CurrCOR.Row2.FromDate",
                dtype=parser.parse,
                if_nan="fill",
                value=dataframe["P1.PD.DOBYear"],
            )
            dataframe = self.change_dtype(
                col_name="P1.PD.CurrCOR.Row2.ToDate",
                dtype=parser.parse,
                if_nan="fill",
                value=dataframe["P3.Sign.C1CertificateIssueDate"],
            )
            # has previous country of residency: bool -> categorical
            dataframe["P1.PD.PCRIndicator"] = dataframe["P1.PD.PCRIndicator"].apply(
                lambda x: True if x == "Y" else False
            )

            # clean previous country of residency features
            country_tag_list = [
                c for c in dataframe.columns.values if "P1.PD.PrevCOR." in c
            ]
            PREV_COUNTRY_MAX_FEATURES = 4
            for i in range(len(country_tag_list) // PREV_COUNTRY_MAX_FEATURES):
                # in XLA extracted file, this section start from `Row2` (ie. i+2)
                i += 2
                # previous country of residency 02: string -> categorical
                dataframe = self.change_dtype(
                    col_name="P1.PD.PrevCOR.Row" + str(i) + ".Country",
                    dtype=str,
                    if_nan="fill",
                    value=CanadaFillna.PREVIOUS_COUNTRY_5257E,
                )
                # previous country of residency status 02: string -> categorical
                dataframe = self.change_dtype(
                    col_name="P1.PD.PrevCOR.Row" + str(i) + ".Status",
                    dtype=np.int8,
                    if_nan="fill",
                    value=np.int8(CanadaFillna.RESIDENCY_STATUS_5257E),
                )
                # previous country of residency 02 period (P1.PD.PrevCOR.Row2): string -> datetime -> int days
                dataframe = self.change_dtype(
                    col_name="P1.PD.PrevCOR.Row" + str(i) + ".FromDate",
                    dtype=parser.parse,
                    if_nan="fill",
                    value=dataframe["P3.Sign.C1CertificateIssueDate"],
                )
                dataframe = self.change_dtype(
                    col_name="P1.PD.PrevCOR.Row" + str(i) + ".ToDate",
                    dtype=parser.parse,
                    if_nan="fill",
                    value=dataframe["P3.Sign.C1CertificateIssueDate"],
                )
            # apply from country of residency (cwa=country where apply): Y=True, N=False
            dataframe["P1.PD.SameAsCORIndicator"] = dataframe[
                "P1.PD.SameAsCORIndicator"
            ].apply(lambda x: True if x == "Y" else False)
            # country where applying: string -> categorical
            dataframe = self.change_dtype(
                col_name="P1.PD.CWA.Row2.Country",
                dtype=str,
                if_nan="fill",
                value=CanadaFillna.COUNTRY_WHERE_APPLYING_5257E,
            )
            # country where applying status: string -> categorical
            dataframe = self.change_dtype(
                col_name="P1.PD.CWA.Row2.Status",
                dtype=np.int8,
                if_nan="fill",
                value=np.int8(CanadaFillna.RESIDENCY_STATUS_5257E),
            )
            # country where applying other: string -> categorical
            dataframe = self.change_dtype(
                col_name="P1.PD.CWA.Row2.Other",
                dtype=bool,
                if_nan="fill",
                value=CanadaFillna.OTHER_DESCRIPTION_INDICATOR_5257E,
            )
            # country where applying period: datetime -> int days
            dataframe = self.change_dtype(
                col_name="P1.PD.CWA.Row2.FromDate",
                dtype=parser.parse,
                if_nan="fill",
                value=dataframe["P3.Sign.C1CertificateIssueDate"],
            )
            dataframe = self.change_dtype(
                col_name="P1.PD.CWA.Row2.ToDate",
                dtype=parser.parse,
                if_nan="fill",
                value=dataframe["P3.Sign.C1CertificateIssueDate"],
            )
            # marriage period: datetime -> int days
            dataframe = self.change_dtype(
                col_name="P1.MS.SecA.DateOfMarr",
                dtype=parser.parse,
                if_nan="fill",
                value=dataframe["P3.Sign.C1CertificateIssueDate"],
            )
            # previous marriage: Y=True, N=False
            dataframe["P2.MS.SecA.PrevMarrIndicator"] = dataframe[
                "P2.MS.SecA.PrevMarrIndicator"
            ].apply(lambda x: True if x == "Y" else False)
            # previous marriage type of relationship
            dataframe = self.change_dtype(
                col_name="P2.MS.SecA.TypeOfRelationship",
                dtype=str,
                if_nan="fill",
                value=CanadaFillna.MARRIAGE_TYPE_5257E,
            )
            # previous spouse age period: string -> datetime -> int days
            dataframe = self.change_dtype(
                col_name="P2.MS.SecA.PrevSpouseDOB.DOBYear",
                dtype=parser.parse,
                if_nan="fill",
                value=dataframe["P3.Sign.C1CertificateIssueDate"],
            )
            # previous marriage period: string -> datetime -> int days
            dataframe = self.change_dtype(
                col_name="P2.MS.SecA.FromDate",
                dtype=parser.parse,
                if_nan="fill",
                value=dataframe["P3.Sign.C1CertificateIssueDate"],
            )
            dataframe = self.change_dtype(
                col_name="P2.MS.SecA.ToDate.ToDate",
                dtype=parser.parse,
                if_nan="fill",
                value=dataframe["P3.Sign.C1CertificateIssueDate"],
            )
            # passport country of issue: string -> categorical
            dataframe = self.change_dtype(
                col_name="P2.MS.SecA.Psprt.CountryofIssue.CountryofIssue",
                dtype=str,
                if_nan="fill",
                value=CanadaFillna.PASSPORT_COUNTRY_5257E,
            )
            # expiry remaining period: datetime -> int days
            # if None, fill with 1 year ago, ie. period=1year
            temp_date = dataframe["P3.Sign.C1CertificateIssueDate"].apply(
                lambda x: x + relativedelta(years=-1)
            )
            dataframe = self.change_dtype(
                col_name="P2.MS.SecA.Psprt.ExpiryDate",
                dtype=parser.parse,
                if_nan="fill",
                value=temp_date,
            )
            # native lang: string -> categorical
            dataframe = self.change_dtype(
                col_name="P2.MS.SecA.Langs.languages.nativeLang.nativeLang",
                dtype=str,
                if_nan="fill",
                value=CanadaFillna.NATIVE_LANG_5257E,
            )
            # communication lang: Eng, Fr, both, none -> categorical
            dataframe = self.change_dtype(
                col_name="P2.MS.SecA.Langs.languages.ableToCommunicate.ableToCommunicate",
                dtype=str,
                if_nan="fill",
                value=CanadaFillna.LANGUAGES_ABLE_TO_COMMUNICATE_5257E,
            )
            # language official test: bool -> binary
            dataframe["P2.MS.SecA.Langs.LangTest"] = dataframe[
                "P2.MS.SecA.Langs.LangTest"
            ].apply(lambda x: True if x == "Y" else False)
            # have national ID: bool -> binary
            dataframe["P2.natID.q1.natIDIndicator"] = dataframe[
                "P2.natID.q1.natIDIndicator"
            ].apply(lambda x: True if x == "Y" else False)
            # national ID country of issue: string -> categorical
            dataframe = self.change_dtype(
                col_name="P2.natID.natIDdocs.CountryofIssue.CountryofIssue",
                dtype=str,
                if_nan="fill",
                value=CanadaFillna.ID_COUNTRY_5257E,
            )
            # United States doc: bool -> binary
            dataframe["P2.USCard.q1.usCardIndicator"] = dataframe[
                "P2.USCard.q1.usCardIndicator"
            ].apply(lambda x: True if x == "Y" else False)
            # US Canada phone number: bool -> binary
            dataframe["P2.CI.cntct.PhnNums.Phn.CanadaUS"] = dataframe[
                "P2.CI.cntct.PhnNums.Phn.CanadaUS"
            ].apply(lambda x: True if x == "1" else False)
            # US Canada alt phone number: bool -> binary
            dataframe["P2.CI.cntct.PhnNums.AltPhn.CanadaUS"] = dataframe[
                "P2.CI.cntct.PhnNums.AltPhn.CanadaUS"
            ].apply(lambda x: True if x == "1" else False)
            # purpose of visit: string, 8 states -> categorical
            dataframe = self.change_dtype(
                col_name="P3.DOV.PrpsRow1.PrpsOfVisit.PrpsOfVisit",
                dtype=np.int8,
                if_nan="fill",
                value=np.int8(CanadaFillna.PURPOSE_OF_VISIT_5257E),
            )  # 7 is other in the form
            # purpose of visit description: string -> binary
            dataframe = self.change_dtype(
                col_name="P3.DOV.PrpsRow1.Other.Other",
                dtype=bool,
                if_nan="fill",
                value=CanadaFillna.OTHER_DESCRIPTION_INDICATOR_5257E,
            )
            # how long going to stay: None -> datetime (0 days)
            dataframe = self.change_dtype(
                col_name="P3.DOV.PrpsRow1.HLS.FromDate",
                dtype=parser.parse,
                if_nan="fill",
                value=dataframe["P3.Sign.C1CertificateIssueDate"],
            )
            dataframe = self.change_dtype(
                col_name="P3.DOV.PrpsRow1.HLS.ToDate",
                dtype=parser.parse,
                if_nan="fill",
                value=dataframe["P3.Sign.C1CertificateIssueDate"],
            )
            # fund to integer
            dataframe = self.change_dtype(
                col_name="P3.DOV.PrpsRow1.Funds.Funds", dtype=np.int32, if_nan="skip"
            )
            # relation to applicant of purpose of visit 01: string -> categorical
            dataframe = self.change_dtype(
                col_name="P3.DOV.cntcts_Row1.RelationshipToMe.RelationshipToMe",
                dtype=str,
                if_nan="fill",
                value=CanadaFillna.CONTACT_TYPE_5257E,
            )
            # relation to applicant of purpose of visit 02: string -> categorical
            dataframe = self.change_dtype(
                col_name="P3.cntcts_Row2.Relationship.RelationshipToMe",
                dtype=str,
                if_nan="fill",
                value=CanadaFillna.CONTACT_TYPE_5257E,
            )
            # higher education: bool -> binary
            dataframe["P3.Edu.EduIndicator"] = dataframe["P3.Edu.EduIndicator"].apply(
                lambda x: True if x == "Y" else False
            )
            # higher education period: string -> datetime -> int days
            dataframe = self.change_dtype(
                col_name="P3.Edu.Edu_Row1.FromYear",
                dtype=parser.parse,
                if_nan="fill",
                value=dataframe["P3.Sign.C1CertificateIssueDate"],
            )
            dataframe = self.change_dtype(
                col_name="P3.Edu.Edu_Row1.ToYear",
                dtype=parser.parse,
                if_nan="fill",
                value=dataframe["P3.Sign.C1CertificateIssueDate"],
            )
            # higher education country: string -> categorical
            dataframe = self.change_dtype(
                col_name="P3.Edu.Edu_Row1.Country.Country",
                dtype=str,
                if_nan="fill",
                value=CanadaFillna.COUNTRY_5257E,
            )
            # field of study: string -> categorical
            dataframe["P3.Edu.Edu_Row1.FieldOfStudy"] = dataframe[
                "P3.Edu.Edu_Row1.FieldOfStudy"
            ].astype("string")
            # clean occupation features
            occupation_tag_list = [
                c for c in dataframe.columns.values if "P3.Occ.OccRow" in c
            ]
            PREV_OCCUPATION_MAX_FEATURES = 9
            for i in range(len(occupation_tag_list) // PREV_OCCUPATION_MAX_FEATURES):
                i += 1  # in the form, it starts from Row1 (ie. i+1)
                # occupation period 01: none -> string year -> int days
                dataframe = self.change_dtype(
                    col_name="P3.Occ.OccRow" + str(i) + ".FromYear",
                    dtype=parser.parse,
                    if_nan="fill",
                    value=dataframe["P3.Sign.C1CertificateIssueDate"],
                )
                dataframe = self.change_dtype(
                    col_name="P3.Occ.OccRow" + str(i) + ".ToYear",
                    dtype=parser.parse,
                    if_nan="fill",
                    value=dataframe["P3.Sign.C1CertificateIssueDate"],
                )

                # occupation type 01: string -> categorical
                dataframe = self.change_dtype(
                    col_name="P3.Occ.OccRow" + str(i) + ".Occ.Occ",
                    dtype=str,
                    if_nan="fill",
                    value=CanadaFillna.OCCUPATION_5257E,
                )
                # occupation country: string -> categorical
                dataframe = self.change_dtype(
                    col_name="P3.Occ.OccRow" + str(i) + ".Country.Country",
                    dtype=str,
                    if_nan="fill",
                    value=CanadaFillna.COUNTRY_5257E,
                )

            # medical details: string -> binary
            dataframe = self.change_dtype(
                col_name="P3.BGI.Details.MedicalDetails",
                dtype=bool,
                if_nan="fill",
                value=CanadaFillna.INDICATOR_FIELD_5257E,
            )
            # other than medical: string -> binary
            dataframe = self.change_dtype(
                col_name="P3.BGI.otherThanMedic",
                dtype=bool,
                if_nan="fill",
                value=CanadaFillna.INDICATOR_FIELD_5257E,
            )
            # without authentication stay, work, etc: bool -> binary
            dataframe["P3.noAuthStay"] = dataframe["P3.noAuthStay"].apply(
                lambda x: True if x == "Y" else False
            )
            # deported or refused entry: bool -> binary
            dataframe["P3.refuseDeport"] = dataframe["P3.refuseDeport"].apply(
                lambda x: True if x == "Y" else False
            )
            # previously applied: bool -> binary
            dataframe["P3.BGI2.PrevApply"] = dataframe["P3.BGI2.PrevApply"].apply(
                lambda x: True if x == "Y" else False
            )
            # criminal record: bool -> binary
            dataframe["P3.PWrapper.criminalRec"] = dataframe[
                "P3.PWrapper.criminalRec"
            ].apply(lambda x: True if x == "Y" else False)
            # military record: bool -> binary
            dataframe["P3.PWrapper.Military.Choice"] = dataframe[
                "P3.PWrapper.Military.Choice"
            ].apply(lambda x: True if x == "Y" else False)
            # political, violent movement record: bool -> binary
            dataframe["P3.PWrapper.politicViol"] = dataframe[
                "P3.PWrapper.politicViol"
            ].apply(lambda x: True if x == "Y" else False)
            # witness of ill treatment: bool -> binary
            dataframe["P3.PWrapper.witnessIllTreat"] = dataframe[
                "P3.PWrapper.witnessIllTreat"
            ].apply(lambda x: True if x == "Y" else False)

            return dataframe

        if type == DocTypes.CANADA_5645E:
            # XFA to XML
            xml = canada_xfa.extract_raw_content(path)
            xml = canada_xfa.clean_xml_for_csv(xml=xml, type=DocTypes.CANADA_5645E)
            # XML to flattened dict
            data_dict = canada_xfa.xml_to_flattened_dict(xml=xml)
            data_dict = canada_xfa.flatten_dict(data_dict)
            # clean flattened dict
            data_dict = functional.dict_summarizer(
                data_dict,
                cutoff_term=CanadaCutoffTerms.CA5645E,
                KEY_ABBREVIATION_DICT=CANADA_5645E_KEY_ABBREVIATION,
                VALUE_ABBREVIATION_DICT=None,
            )

            # convert each data dict to a dataframe
            dataframe = pd.DataFrame.from_dict(data=[data_dict], orient="columns")
            self.dataframe = dataframe

            # drop pepeg columns
            #   warning: setting `errors='ignore` ignores errors if columns do not exist!
            dataframe.drop(
                CANADA_5645E_DROP_COLUMNS, axis=1, inplace=True, errors="ignore"
            )

            # transform multiple pleb columns into a single chad one and fixing column dtypes
            # type of application: (already onehot) string -> int
            cols = [col for col in dataframe.columns.values if "p1.Subform1" in col]
            for c in cols:
                dataframe = self.change_dtype(
                    col_name=c,
                    dtype=np.int16,
                    if_nan="fill",
                    value=np.int16(CanadaFillna.VISA_APPLICATION_TYPE_5645E),
                )
            # drop all Accompany=No and only rely on Accompany=Yes using binary state
            self.column_dropper(string="No", inplace=True)
            # applicant marriage status: string to integer
            dataframe = self.change_dtype(
                col_name="p1.SecA.App.ChdMStatus",
                dtype=np.int16,
                if_nan="fill",
                value=np.int16(CanadaFillna.CHILD_MARRIAGE_STATUS_5645E),
            )
            # validation date of information, i.e. current date: datetime
            dataframe = self.change_dtype(
                col_name="p1.SecC.SecCdate",
                dtype=parser.parse,
                if_nan="fill",
                value=self.base_date,
            )
            # spouse date of birth: string -> datetime
            dataframe = self.change_dtype(
                col_name="p1.SecA.Sps.SpsDOB",
                dtype=parser.parse,
                if_nan="fill",
                value=dataframe["p1.SecC.SecCdate"],
            )

            # spouse country of birth: string -> categorical
            dataframe = self.change_dtype(
                col_name="p1.SecA.Sps.SpsCOB", dtype=str, if_nan="skip"
            )
            # spouse occupation type (issue #2): string -> categorical
            dataframe = self.change_dtype(
                col_name="p1.SecA.Sps.SpsOcc",
                dtype=str,
                if_nan="fill",
                value=CanadaFillna.OCCUPATION_5257E,
            )
            # spouse accompanying: coming=True or not_coming=False
            dataframe["p1.SecA.Sps.SpsAccomp"] = dataframe[
                "p1.SecA.Sps.SpsAccomp"
            ].apply(lambda x: True if x == "1" else False)
            # mother date of birth: string -> datetime
            dataframe = self.change_dtype(
                col_name="p1.SecA.Mo.MoDOB",
                dtype=parser.parse,
                if_nan="fill",
                value=dataframe["p1.SecC.SecCdate"],
            )

            # mother occupation type (issue #2): string -> categorical
            dataframe = self.change_dtype(
                col_name="p1.SecA.Mo.MoOcc",
                dtype=str,
                if_nan="fill",
                value=CanadaFillna.OCCUPATION_5257E,
            )
            # mother marriage status: int -> categorical
            dataframe = self.change_dtype(
                col_name="p1.SecA.Mo.ChdMStatus",
                dtype=np.int16,
                if_nan="fill",
                value=np.int16(CanadaFillna.CHILD_MARRIAGE_STATUS_5645E),
            )
            # mother accompanying: coming=True or not_coming=False
            dataframe["p1.SecA.Mo.MoAccomp"] = dataframe["p1.SecA.Mo.MoAccomp"].apply(
                lambda x: True if x == "1" else False
            )
            # father date of birth: string -> datetime
            dataframe = self.change_dtype(
                col_name="p1.SecA.Fa.FaDOB",
                dtype=parser.parse,
                if_nan="fill",
                value=dataframe["p1.SecC.SecCdate"],
            )

            # mother occupation type (issue #2): string -> categorical
            dataframe = self.change_dtype(
                col_name="p1.SecA.Fa.FaOcc",
                dtype=str,
                if_nan="fill",
                value=CanadaFillna.OCCUPATION_5257E,
            )
            # father marriage status: int -> categorical
            dataframe = self.change_dtype(
                col_name="p1.SecA.Fa.ChdMStatus",
                dtype=np.int16,
                if_nan="fill",
                value=np.int16(CanadaFillna.CHILD_MARRIAGE_STATUS_5645E),
            )
            # father accompanying: coming=True or not_coming=False
            dataframe["p1.SecA.Fa.FaAccomp"] = dataframe["p1.SecA.Fa.FaAccomp"].apply(
                lambda x: True if x == "1" else False
            )

            # children's status
            children_tag_list = [
                c for c in dataframe.columns.values if "p1.SecB.Chd" in c
            ]
            CHILDREN_MAX_FEATURES = 7
            for i in range(len(children_tag_list) // CHILDREN_MAX_FEATURES):
                # child's marriage status 01: string to integer
                dataframe = self.change_dtype(
                    col_name="p1.SecB.Chd.[" + str(i) + "].ChdMStatus",
                    dtype=np.int16,
                    if_nan="fill",
                    value=np.int16(CanadaFillna.CHILD_MARRIAGE_STATUS_5645E),
                )
                # child's relationship 01: string -> categorical
                dataframe = self.change_dtype(
                    col_name="p1.SecB.Chd.[" + str(i) + "].ChdRel",
                    dtype=str,
                    if_nan="fill",
                    value=CanadaFillna.CHILD_RELATION_5645E,
                )
                # child's date of birth 01: string -> datetime
                dataframe = self.change_dtype(
                    col_name="p1.SecB.Chd.[" + str(i) + "].ChdDOB",
                    dtype=parser.parse,
                    if_nan="skip",
                )

                # child's country of birth 01: string -> categorical
                dataframe = self.change_dtype(
                    col_name="p1.SecB.Chd.[" + str(i) + "].ChdCOB",
                    dtype=str,
                    if_nan="fill",
                    value=CanadaFillna.COUNTRY_5257E,
                )
                # child's occupation type 01 (issue #2): string -> categorical
                dataframe = self.change_dtype(
                    col_name="p1.SecB.Chd.[" + str(i) + "].ChdOcc",
                    dtype=str,
                    if_nan="fill",
                    value=CanadaFillna.OCCUPATION_5257E,
                )
                # child's marriage status: int -> categorical
                dataframe = self.change_dtype(
                    col_name="p1.SecB.Chd.[" + str(i) + "].ChdMStatus",
                    dtype=np.int16,
                    if_nan="fill",
                    value=np.int16(CanadaFillna.CHILD_MARRIAGE_STATUS_5645E),
                )
                # child's accompanying 01: coming=True or not_coming=False
                dataframe["p1.SecB.Chd.[" + str(i) + "].ChdAccomp"] = dataframe[
                    "p1.SecB.Chd.[" + str(i) + "].ChdAccomp"
                ].apply(lambda x: True if x == "1" else False)

                # check if the child does not exist and fill it properly (ghost case monkaS)
                if (
                    (
                        dataframe["p1.SecB.Chd.[" + str(i) + "].ChdMStatus"]
                        == CanadaFillna.CHILD_MARRIAGE_STATUS_5645E
                    ).all()
                    and (
                        dataframe["p1.SecB.Chd.[" + str(i) + "].ChdRel"] == "OTHER"
                    ).all()
                    and (dataframe["p1.SecB.Chd.[" + str(i) + "].ChdDOB"].isna()).all()
                    and (
                        dataframe["p1.SecB.Chd.[" + str(i) + "].ChdAccomp"] == False
                    ).all()
                ):
                    # ghost child's date of birth: None -> datetime (current date) -> 0 days
                    dataframe = self.change_dtype(
                        col_name="p1.SecB.Chd.[" + str(i) + "].ChdDOB",
                        dtype=parser.parse,
                        if_nan="fill",
                        value=dataframe["p1.SecC.SecCdate"],
                    )

            # siblings' status
            siblings_tag_list = [
                c for c in dataframe.columns.values if "p1.SecC.Chd" in c
            ]
            SIBLINGS_MAX_FEATURES = 8
            for i in range(len(siblings_tag_list) // SIBLINGS_MAX_FEATURES):
                # sibling's marriage status 01: string to integer
                dataframe = self.change_dtype(
                    col_name="p1.SecC.Chd.[" + str(i) + "].ChdMStatus",
                    dtype=np.int16,
                    if_nan="fill",
                    value=np.int16(CanadaFillna.CHILD_MARRIAGE_STATUS_5645E),
                )
                # sibling's relationship 01: string -> categorical
                dataframe = self.change_dtype(
                    col_name="p1.SecC.Chd.[" + str(i) + "].ChdRel",
                    dtype=str,
                    if_nan="fill",
                    value=CanadaFillna.CHILD_RELATION_5645E,
                )
                # sibling's date of birth 01: string -> datetime
                dataframe = self.change_dtype(
                    col_name="p1.SecC.Chd.[" + str(i) + "].ChdDOB",
                    dtype=parser.parse,
                    if_nan="skip",
                )

                # sibling's country of birth 01: string -> categorical
                dataframe = self.change_dtype(
                    col_name="p1.SecC.Chd.[" + str(i) + "].ChdCOB",
                    dtype=str,
                    if_nan="fill",
                    value=CanadaFillna.COUNTRY_5257E,
                )
                # sibling's occupation type 01 (issue #2): string -> categorical
                dataframe = self.change_dtype(
                    col_name="p1.SecC.Chd.[" + str(i) + "].ChdOcc",
                    dtype=str,
                    if_nan="fill",
                    value=CanadaFillna.OCCUPATION_5257E,
                )
                # sibling's accompanying: coming=True or not_coming=False
                dataframe["p1.SecC.Chd.[" + str(i) + "].ChdAccomp"] = dataframe[
                    "p1.SecC.Chd.[" + str(i) + "].ChdAccomp"
                ].apply(lambda x: True if x == "1" else False)

                # check if the sibling does not exist and fill it properly (ghost case monkaS)
                if (
                    (
                        dataframe["p1.SecC.Chd.[" + str(i) + "].ChdMStatus"]
                        == CanadaFillna.CHILD_MARRIAGE_STATUS_5645E
                    ).all()
                    and (
                        dataframe["p1.SecC.Chd.[" + str(i) + "].ChdRel"] == "OTHER"
                    ).all()
                    and (dataframe["p1.SecC.Chd.[" + str(i) + "].ChdOcc"].isna()).all()
                    and (
                        dataframe["p1.SecC.Chd.[" + str(i) + "].ChdAccomp"] == False
                    ).all()
                ):
                    # ghost sibling's date of birth: None -> datetime (current date) -> 0 days
                    dataframe = self.change_dtype(
                        col_name="p1.SecC.Chd.[" + str(i) + "].ChdDOB",
                        dtype=parser.parse,
                        if_nan="fill",
                        value=dataframe["p1.SecC.SecCdate"],
                    )

            return dataframe

        if type == DocTypes.CANADA_LABEL:
            dataframe = pd.read_csv(path, sep=" ", names=["VisaResult"])
            functional.change_dtype(
                dataframe=dataframe,
                col_name="VisaResult",
                dtype=np.int8,
                if_nan="fill",
                value=np.int8(CanadaFillna.VISA_RESULT),
            )
            return dataframe


class FileTransform:
    """A base class for applying transforms as a composable object over files.

    Any behavior over the files itself (not the content of files)
    must extend this class.

    """

    def __init__(self) -> None:
        pass

    def __call__(self, src: str, dst: str, *args: Any, **kwds: Any) -> Any:
        """

        Args:
            src (str): source file to be processed
            dst (str): the pass that the processed file to be saved
        """
        pass


class CopyFile(FileTransform):
    """Only copies a file, a wrapper around `shutil`'s copying methods

    Default is set to 'cf', i.e. `shutil.copyfile`. For more info see
    shutil_ documentation.


    Reference:
        1. https://stackoverflow.com/a/30359308/18971263
    """

    def __init__(self, mode: str) -> None:
        super().__init__()

        self.COPY_MODES = ["c", "cf", "c2"]
        self.mode = mode if mode is not None else "cf"
        self.__check_mode(mode=mode)

    def __call__(self, src: str, dst: str, *args: Any, **kwds: Any) -> Any:
        if self.mode == "c":
            shutil.copy(src=src, dst=dst)
        elif self.mode == "cf":
            shutil.copyfile(src=src, dst=dst)
        elif self.mode == "c2":
            shutil.copy2(src=src, dst=dst)

    def __check_mode(self, mode: str):
        """Checks copying mode to be available in shutil_

        Args:
            mode: copying mode in `shutil`, one of `'c'`, `'cf'`, `'c2'`

        .. _shutil: https://docs.python.org/3/library/shutil.html
        """
        if not mode in self.COPY_MODES:
            raise ValueError(
                (f"Mode {mode} does not exist,", f'choose one of "{self.COPY_MODES}".')
            )


class MakeContentCopyProtectedMachineReadable(FileTransform):
    """Reads a 'content-copy' protected PDF and removes this restriction

    Removing the protection is done by saving a "printed" version of via pikepdf_

    References:
        1. https://www.reddit.com/r/Python/comments/t32z2o/simple_code_to_unlock_all_readonly_pdfs_in/
        2. https://pikepdf.readthedocs.io/en/latest/

    .. _pikepdf: https://pikepdf.readthedocs.io/en/latest/
    """

    def __init__(self) -> None:
        super().__init__()

    def __call__(self, src: str, dst: str, *args: Any, **kwds: Any) -> Any:
        """

        Args:
            src (str): source file to be processed
            dst (str): destination to save the processed file

        Returns:
            Any: None
        """
        pdf = pikepdf.open(src, allow_overwriting_input=True)
        pdf.save(dst)


class FileTransformCompose:
    """Composes several transforms operating on files together

    The transforms should be tied to files with keyword and this will be only applying
    functions on files that match the keyword using a dictionary

    Transformation dictionary over files in the following structure::

        {
            FileTransform: 'filter_str',
            ...,
        }

    Note:
        Transforms will be applied in order of the keys in the dictionary
    """

    def __init__(self, transforms: dict[FileTransform, str]) -> None:
        """

        Args:
            transforms (dict[FileTransform, str]): a dictionary of transforms, where the key is the instance of
                FileTransform and the value is the keyword that the transform will be
                applied to

        Raises:
            ValueError: if the keyword is not a string
        """
        if transforms is not None:
            for k in transforms.keys():
                if not issubclass(k.__class__, FileTransform):
                    raise TypeError(f"Keys must be {FileTransform} instance.")

        self.transforms = transforms

    def __call__(self, src: str, dst: str, *args: Any, **kwds: Any) -> Any:
        """Applies transforms in order

        Args:
            src (str): source file path to be processed
            dst (str): destination to save the processed file
        """
        for transform, file_filter in self.transforms.items():
            if file_filter in src:
                transform(src, dst)
