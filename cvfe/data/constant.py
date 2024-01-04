__all__ = [
    "CANADA_5257E_KEY_ABBREVIATION",
    "CANADA_5645E_KEY_ABBREVIATION",
    "CANADA_5257E_VALUE_ABBREVIATION",
    "CANADA_5257E_DROP_COLUMNS",
    "CANADA_5645E_DROP_COLUMNS",
    "DocTypes",
    "CanadaCutoffTerms",
    "CanadaFillna",
    "DATEUTIL_DEFAULT_DATETIME",
    "T0",
    # Data Enums shared all over the place
    "CustomNamingEnum",
    "CanadaMarriageStatus",
    "CanadaContactRelation",
    "CanadaResidencyStatus",
    "Sex",
]

import datetime
from enum import Enum, auto
from types import DynamicClassAttribute
from typing import List

# DICTIONARY
CANADA_5257E_KEY_ABBREVIATION = {
    "Page": "P",
    "PersonalDetails": "PD",
    "CountryWhereApplying": "CWA",
    "MaritalStatus": "MS",
    "Section": "Sec",
    "ContactInformation": "CI",
    "DetailsOfVisit": "DOV",
    "Education": "Edu",
    "PageWrapper": "PW",
    "Occupation": "Occ",
    "BackgroundInfo": "BGI",
    "Current": "Curr",
    "Previous": "Prev",
    "Marriage": "Marr",
    "Married": "Marr",
    "Previously": "Prev",
    "Passport": "Psprt",
    "Language": "Lang",
    "Address": "Addr",
    "contact": "cntct",
    "Contact": "cntct",
    "Resident": "Resi",
    "Phone": "Phn",
    "Number": "Num",
    "Purpose": "Prps",
    "HowLongStay": "HLS",
    "Signature": "Sign",
    # more meaningful keys
    "GovPosition.Choice": "witnessIllTreat",
    "Occ.Choice": "politicViol",
    "BGI3.Choice": "criminalRec",
    "Details.VisaChoice3": "PrevApply",
    "BGI2.VisaChoice2": "refuseDeport",
    "BGI2.VisaChoice1": "noAuthStay",
    "backgroundInfoCalc": "otherThanMedic",
}
"""Dict of abbreviation used to shortening length of KEYS in XML to CSV conversion

"""

CANADA_5645E_KEY_ABBREVIATION = {
    "page": "p",
    "Applicant": "App",
    "Mother": "Mo",
    "Father": "Fa",
    "Section": "Sec",
    "Spouse": "Sps",
    "Child": "Chd",
    "Address": "Addr",
    "Occupation": "Occ",
    "Yes": "Accomp",
    "Relationship": "Rel",
}
"""Dict of abbreviation used to shortening length of KEYS in XML to CSV conversion

"""

# see #29
DATEUTIL_DEFAULT_DATETIME = {
    "day": 1,  # no reason for this value (CluelessClown)
    "month": 1,  # no reason for this value (CluelessClown)
    "year": datetime.MINYEAR,
}
"""A default date for the ``dateutil.parser.parse`` function when some part of date is not provided

"""

CANADA_5257E_VALUE_ABBREVIATION = {
    "BIOMETRIC ENROLMENT": "Bio",
    "223": "IRAN",
    "045": "TURKEY",
}
"""Dict of abbreviation used to shortening length of VALUES in XML to CSV conversion
"""

# LIST
CANADA_5257E_DROP_COLUMNS = [
    # newly rolled back data
    # 'P1.PD.DOBDay', 'P1.PD.DOBMonth', 'P1.PrevSpouseAge', 'P1.PD.Name.FamilyName',
    # 'P1.PD.Name.GivenName', 'P1.PD.PrevCOR.Row2.Other', 'P1.MS.SecA.FamilyName',
    # 'P1.MS.SecA.GivenName', 'P2.MS.SecA.PrevSpouseDOB.DOBMonth',
    # 'P2.MS.SecA.PrevSpouseDOB.DOBDay', 'P2.MS.SecA.Psprt.PsprtNum.PsprtNum',
    # 'P2.natID.natIDdocs.DocNum.DocNum', 'P2.MS.SecA.Langs.languages.lov',
    # 'P3.Occ.OccRow1.Employer', 'P3.Occ.OccRow2.Employer', 'P3.Occ.OccRow3.Employer',
    # 'P1.Age', 'P3.BGI2.Details.refusedDetails', 'P3.PWrapper.BGI3.details',
    # 'P3.PWrapper.Military.militaryServiceDetails', 'P1.PD.AliasName.AliasGivenName',
    # 'P1.PD.AliasName.AliasFamilyName', 'P2.MS.SecA.PMFamilyName',
    # 'P2.MS.SecA.GivenName.PMGivenName', 'P3.DOV.cntcts_Row1.Name.Name',
    # 'P3.cntcts_Row2.Name.Name', 'P1.PD.PrevCOR.Row3.Other',
    # 'P3.cntcts_Row2.AddrInCanada.AddrInCanada', 'P3.Edu.Edu_Row1.FromMonth',
    # 'P3.Edu.Edu_Row1.ToMonth', 'P3.Edu.Edu_Row1.School', 'P3.Edu.Edu_Row1.CityTown',
    # 'P3.Edu.Edu_Row1.ProvState', 'P3.Occ.OccRow1.FromMonth', 'P3.Occ.OccRow1.ToMonth',
    # 'P3.Occ.OccRow1.CityTown.CityTown', 'P3.Occ.OccRow1.ProvState', 'P3.Occ.OccRow2.FromMonth',
    # 'P3.Occ.OccRow2.ToMonth', 'P3.Occ.OccRow2.CityTown.CityTown', 'P3.Occ.OccRow2.ProvState',
    # 'P3.Occ.OccRow3.FromMonth', 'P3.Occ.OccRow3.ToMonth', 'P3.Occ.OccRow3.CityTown.CityTown',
    # 'P3.Occ.OccRow3.ProvState', 'P3.DOV.cntcts_Row1.AddrInCanada.AddrInCanada',
    # 'P2.CI.cntct.FaxEmail.Email', 'P2.CI.cntct.AddrRow1.POBox.POBox',
    # 'P2.CI.cntct.AddrRow1.Apt.AptUnit', 'P2.CI.cntct.AddrRow1.StreetNum.StreetNum',
    # 'P2.CI.cntct.AddrRow1.Streetname.Streetname', 'P2.CI.cntct.AddrRow2.ProvinceState.ProvinceState',
    # 'P2.CI.cntct.AddrRow2.PostalCode.PostalCode', 'P2.CI.cntct.AddrRow2.District',
    # 'P2.CI.cntct.ResiialAddrRow1.AptUnit.AptUnit', 'P2.CI.cntct.ResiialAddrRow1.StreetNum.StreetNum',
    # 'P2.CI.cntct.ResiialAddrRow1.StreetName.Streetname', 'P2.CI.cntct.ResiialAddrRow2.District',
    # 'P2.CI.cntct.ResiialAddrRow2.ProvinceState.ProvinceState', 'P2.CI.cntct.PhnNums.Phn.NumCountry',
    # 'P2.CI.cntct.ResiialAddrRow2.PostalCode.PostalCode', 'P2.CI.cntct.PhnNums.Phn.ActualNum',
    # 'P2.CI.cntct.PhnNums.Phn.NANum.AreaCode', 'P2.CI.cntct.PhnNums.Phn.NANum.FirstThree',
    # 'P2.CI.cntct.PhnNums.Phn.NANum.LastFive', 'P2.CI.cntct.PhnNums.Phn.IntlNum.IntlNum',
    # 'P2.CI.cntct.PhnNums.AltPhn.NumCountry', 'P2.CI.cntct.PhnNums.AltPhn.ActualNum',
    # 'P2.CI.cntct.PhnNums.AltPhn.NANum.AreaCode', 'P2.CI.cntct.PhnNums.AltPhn.NANum.FirstThree',
    # 'P2.CI.cntct.PhnNums.AltPhn.NANum.LastFive', 'P2.CI.cntct.PhnNums.AltPhn.IntlNum.IntlNum',
    # 'P2.CI.cntct.FaxEmail.Phn.CanadaUS', 'P2.CI.cntct.FaxEmail.Phn.Other',
    # 'P2.CI.cntct.FaxEmail.Phn.NumExt', 'P2.MS.SecA.Psprt.IssueDate.IssueDate',
    # 'P2.CI.cntct.FaxEmail.Phn.NumCountry', 'P2.CI.cntct.FaxEmail.Phn.ActualNum',
    # 'P2.CI.cntct.FaxEmail.Phn.NANum.AreaCode', 'P2.CI.cntct.FaxEmail.Phn.NANum.FirstThree',
    # 'P2.CI.cntct.FaxEmail.Phn.NANum.LastFive', 'P2.CI.cntct.FaxEmail.Phn.IntlNum.IntlNum',
    # 'P2.MS.SecA.Psprt.IssueYYYY', 'P2.MS.SecA.Psprt.IssueMM', 'P2.MS.SecA.Psprt.IssueDD',
    # 'P2.MS.SecA.Psprt.expiryYYYY', 'P2.MS.SecA.Psprt.expiryMM', 'P2.MS.SecA.Psprt.expiryDD',
    # 'P2.natID.natIDdocs.IssueDate.IssueDate', 'P2.natID.natIDdocs.ExpiryDate',
    # 'P2.MS.SecA.Psprt.TaiwanPIN', 'P2.MS.SecA.Psprt.IsraelPsprtIndicator',
    # 'P2.USCard.usCarddocs.ExpiryDate', 'P2.USCard.usCarddocs.DocNum.DocNum',
    # 'P2.MS.SecA.DateLastValidated.DateCalc', 'P2.MS.SecA.DateLastValidated.Day',
    # 'P2.MS.SecA.DateLastValidated.Year', 'P2.MS.SecA.DateLastValidated.Month',
    "ns0:datasets.@xmlns:ns0",
    "P1.Header.CRCNum",
    "P1.FormVersion",
    "P1.PD.UCIClientID",
    "P1.PD.SecHeader.@ns0:dataNode",
    "P1.PD.CurrCOR.Row1.@ns0:dataNode",
    "P1.PD.PrevCOR.Row1.@ns0:dataNode",
    "P1.PD.CWA.Row1.@ns0:dataNode",
    "P1.PD.ApplicationValidatedFlag",
    "P2.MS.SecA.SecHeader.@ns0:dataNode",
    "P2.MS.SecA.PsprtSecHeader.@ns0:dataNode",
    "P2.MS.SecA.Langs.languagesHeader.@ns0:dataNode",
    "P2.natID.SecHeader.@ns0:dataNode",
    "P2.USCard.SecHeader.@ns0:dataNode",
    "P2.USCard.SecHeader.@ns0:dataNode",
    "P2.CI.cntct.cntctInfoSecHeader.@ns0:dataNode",
    "P3.SecHeader_DOV.@ns0:dataNode",
    "P3.Edu.Edu_SecHeader.@ns0:dataNode",
    "P3.Occ.SecHeader_CurrOcc.@ns0:dataNode",
    "P3.BGI_SecHeader.@ns0:dataNode",
    "P3.Sign.Consent0.Choice",
    "P3.Sign.hand.@ns0:dataNode",
    "P3.Sign.TextField2",
    "P3.Disclosure.@ns0:dataNode",
    "P3.ReaderInfo",
    "Barcodes.@ns0:dataNode",
]
"""List of columns to be dropped before doing any preprocessing

Note:
    This list has been determined manually.

"""

CANADA_5645E_DROP_COLUMNS = {
    # newly rolled back data
    # 'p1.SecA.App.AppDOB', 'p1.SecA.App.AppCOB', 'p1.SecA.App.AppOcc',
    # 'p1.SecA.Sps.ChdMStatus', 'p1.SecA.App.AppOcc',
    "xfa:datasets.@xmlns:xfa",
    "p1.SecA.Title.@xfa:dataNode",
    "p1.SecB.SecBsignature",
    "p1.SecB.SecBdate",
    "p1.SecC.Title.@xfa:dataNode",
    "p1.SecA.SecAsignature",
    "p1.SecA.SecAdate",
    "p1.SecB.Title.@xfa:dataNode",
    "p1.SecC.SecCsignature",
    "p1.SecC.Subform2.@xfa:dataNode",
    "formNum",
}
"""List of columns to be dropped before doing any preprocessing

Note:
    This list has been determined manually.

"""


# ENUM
class DocTypes(Enum):
    """Contains all document types which can be used to customize ETL steps for each document type

    Members follow the ``<country_name>_<document_type>`` naming convention. The value
    and its order are meaningless.
    """

    CANADA = 1  # referring to all Canada docs in general
    CANADA_5257E = 2  # application for visitor visa (temporary resident visa)
    CANADA_5645E = 3  # Family information
    CANADA_LABEL = 4  # containing labels


class CanadaCutoffTerms:
    """Dict of cut off terms for different files that is can be used with :func:`vizard.data.functional.dict_summarizer"""

    CA5645E = "IMM_5645"
    CA5257E = "form1"


class CanadaFillna:
    """Values used to fill ``None`` s depending on the form structure

    Members follow the ``<field_name>_<form_name>`` naming convention. The value
    has been extracted by manually inspecting the documents. Hence, for each
    form, user must find and set this value manually.

    Note:
        We do not use any heuristics here, we just follow what form used and
        only add another option which should be used as ``None`` state; i.e. ``None``
        as a separate feature in categorical mode.
    """

    # 5257e
    COUNTRY_CODE_5257E = "Unknown"
    VISA_TYPE_5257E = "OTHER"
    PLACE_BIRTH_CITY_5257E = "OTHER"
    COUNTRY_5257E = "IRAN"
    CITIZENSHIP_5257E = "IRAN"
    RESIDENCY_STATUS_5257E = 6
    OTHER_DESCRIPTION_INDICATOR_5257E = False
    PREVIOUS_COUNTRY_5257E = "OTHER"
    COUNTRY_WHERE_APPLYING_5257E = "OTHER"
    MARRIAGE_TYPE_5257E = "OTHER"
    PASSPORT_COUNTRY_5257E = "OTHER"
    NATIVE_LANG_5257E = "IRAN"
    LANGUAGES_ABLE_TO_COMMUNICATE_5257E = "NEITHER"
    ID_COUNTRY_5257E = "IRAN"
    PURPOSE_OF_VISIT_5257E = 7
    CONTACT_TYPE_5257E = "OTHER"
    OCCUPATION_5257E = "OTHER"
    INDICATOR_FIELD_5257E = False

    # 5645e
    VISA_APPLICATION_TYPE_5645E = "0"
    CHILD_MARRIAGE_STATUS_5645E = 9
    CHILD_RELATION_5645E = "OTHER"

    # Visa result (manual file created by me :D)
    VISA_RESULT = 0


class CustomNamingEnum(Enum):
    """Extends base :class:`enum.Enum` to support custom naming for members

    Note:
        Class attribute :attr:`name` has been overridden to return the name
        of a marital status that matches with the dataset and not the ``Enum``
        naming convention of Python. For instance, ``COMMON_LAW`` -> ``common-law`` in
        case of Canada forms.

    Note:
        Devs should subclass this class and add their desired members in newly
        created classes. E.g. see :class:`CanadaMarriageStatus`

    Note:
        Classes that subclass this, for values of their members should use :class:`enum.auto`
        to demonstrate that chosen value is not domain-specific. Otherwise, any explicit
        value given to members should implicate a domain-specific (e.g. extracted from dataset)
        value. Values that are explicitly provided are the values used in original data. Hence,
        it should not be modified by any means as it is tied to dataset, transformation,
        and other domain-specific values. E.g. compare values in :class:`CanadaMarriageStatus`
        and :class:`SiblingRelation`.
    """

    @DynamicClassAttribute
    def name(self):
        _name = super(CustomNamingEnum, self).name
        _name: str = _name.lower()
        # convert FOO_BAR to foo-bar (dataset convention)
        _name = _name.replace("_", "-")
        self._name_ = _name
        return self._name_

    @classmethod
    def get_member_names(cls):
        _member_names_: List[str] = []
        for mem_name in cls._member_names_:
            _member_names_.append(cls._member_map_[mem_name].name)
        return _member_names_


class CanadaMarriageStatus(CustomNamingEnum):
    """States of marriage in Canada forms

    Note:
        Values for the members are the values used in original Canada forms. Hence,
        it should not be modified by any means as it is tied to dataset, transformation,
        and other domain-specific values.
    """

    COMMON_LAW = 2
    DIVORCED = 3
    SEPARATED = 4
    MARRIED = 5
    SINGLE = 7
    WIDOWED = 8
    UNKNOWN = 9


class CanadaContactRelation(CustomNamingEnum):
    """Contact relation in Canada data"""

    F1 = auto()
    F2 = auto()
    HOTEL = auto()
    WORK = auto()
    FRIEND = auto()
    UKN = auto()


class CanadaResidencyStatus(CustomNamingEnum):
    """Residency status in a country in Canada data"""

    CITIZEN = 1
    VISITOR = 3
    OTHER = 6


class Sex(CustomNamingEnum):
    """Sex types in general"""

    FEMALE = auto()
    MALE = auto()

    @DynamicClassAttribute
    def name(self):
        _name = super(CustomNamingEnum, self).name
        # convert foobar to Foobar (i.e. Female, Male)
        _name: str = _name.lower().capitalize()
        self._name_ = _name
        return self._name_


T0 = "19000202T000000"
"""a default meaningless time to fill the `None`s
"""
