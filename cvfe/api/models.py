__all__ = [
    'PredictionResponse', 'Payload',
    'CanadaMarriageStatusResponse',
    'ChildRelationResponse', 'CanadaContactRelationResponse', 'CanadaResidencyStatusResponse',
    'EducationFieldOfStudyResponse', 'XaiResponse', 'XaiAggregatedGroupResponse'
]

# core
import pydantic
from pydantic import validator
import json
# ours
from cvfe.data.constant import (
    CanadaMarriageStatus,
    CanadaContactRelation,
    CanadaResidencyStatus,
    Sex,
    EducationFieldOfStudy
)
# helpers
from typing import Any, Dict, List, Tuple


class BaseModel(pydantic.BaseModel):
    """Extension of :class:`pydantic.BaseModel` to parse ``File`` and ``Form`` data along side each other

    Reference:
        * https://stackoverflow.com/a/70640522/18971263
    """
    def __init__(__pydantic_self__, **data: Any) -> None:
        super().__init__(**data)

    @classmethod
    def __get_validators__(cls):
        yield cls._validate_from_json_string

    @classmethod
    def _validate_from_json_string(cls, value):
        if isinstance(value, str):
            return cls.validate(json.loads(value.encode()))
        return cls.validate(value)


class PredictionResponse(BaseModel):
    """Response model for the prediction of machine learning model

    Note:
        This is the final goal of the project from technical aspect
    """
    result: float


class Payload(BaseModel):

    sex: str

    @validator('sex')
    def _sex(cls, value):
        if value not in Sex.get_member_names():
            raise ValueError(f'"{value}" is not valid.'
                             f' Only "{Sex.get_member_names()}" are available.')
        return value

    country_where_applying_country: str = 'TURKEY'
    country_where_applying_status: str = 'OTHER'

    @validator(
        'country_where_applying_status'
    )
    def _residence_status(cls, value):
        value = value.lower().strip()
        if value not in CanadaResidencyStatus.get_member_names():
            raise ValueError(f'"{value}" is not valid')
        return value

    previous_marriage_indicator: bool = False

    purpose_of_visit: str = 'tourism'
    funds: float = 8000.

    @validator('funds')
    def _funds(cls, value):
        if value <= 0.:
            raise ValueError('funds cannot be negative number.')
        return value

    contact_relation_to_me: str = 'hotel'
    contact_relation_to_me2: str = 'ukn'

    @validator(
        'contact_relation_to_me',
        'contact_relation_to_me2'
    )
    def _contact_relation_to_me(cls, value):
        value = value.lower().strip()
        if value not in CanadaContactRelation.get_member_names():
            raise ValueError(f'"{value}" is not valid')
        return value


    education_field_of_study: str = 'unedu'

    @validator('education_field_of_study')
    def _education_field_of_study(cls, value):
        value = value.lower().strip()
        if value not in EducationFieldOfStudy.get_member_names():
            raise ValueError(f'"{value}" is not valid')
        return value


    occupation_title1: str = 'OTHER'
    occupation_title2: str = 'OTHER'
    occupation_title3: str = 'OTHER'

    no_authorized_stay: bool = False
    refused_entry_or_deport: bool = False
    previous_apply: bool = False

    date_of_birth: float

    @validator('date_of_birth')
    def _date_of_birth(cls, value):
        if value < 18:
            raise ValueError('This service only accepts adults')
        return value

    country_where_applying_period: float = 30.  # days

    @validator('country_where_applying_period')
    def _country_where_applying_period(cls, value):
        if value < 0:
            raise ValueError('Value cannot be negative')
        return value

    marriage_period: float = 0.  # years
    previous_marriage_period: float = 0.  # years

    @validator(
        'marriage_period',
        'previous_marriage_period'
    )
    def _marriage_period(cls, value):
        if value < 0:
            raise ValueError('Value cannot be negative')
        return value

    passport_expiry_date_remaining: float = 3.  # years

    @validator('passport_expiry_date_remaining')
    def _passport_expiry_date_remaining(cls, value):
        if (value < 0) and (value > 10):
            raise ValueError('Value cannot be negative or > 10')
        return value

    how_long_stay_period: float = 30.  # days

    @validator('how_long_stay_period')
    def _how_long_stay_period(cls, value):
        if value < 0:
            raise ValueError('Value cannot be negative')
        return value

    education_period: float = 0.  # years

    @validator('education_period')
    def _education_period(cls, value):
        if (value < 0) and (value > 10):
            raise ValueError('Value cannot be negative')
        return value

    occupation_period: float = 0.   # years
    occupation_period2: float = 0.  # years
    occupation_period3: float = 0.  # years

    @validator(
        'occupation_period',
        'occupation_period2',
        'occupation_period3'
    )
    def _occupation_period(cls, value):
        if value < 0:
            raise ValueError('Value cannot be negative')
        return value

    applicant_marital_status: str = 'single'

    
    @validator(
        'applicant_marital_status',
    )
    def _marital_status(cls, value):
        value = value.lower().strip()
        if value not in CanadaMarriageStatus.get_member_names():
            raise ValueError(f'"{value}" is not valid')
        return value

    previous_country_of_residence_count: int = 0

    @validator('previous_country_of_residence_count')
    def _previous_country_of_residence_count(cls, value):
        if (value < 0) and (value > 5):
            raise ValueError('Value cannot be negative or > 5')
        return value

    sibling_foreigner_count: int = 0

    @validator('sibling_foreigner_count')
    def _sibling_foreigner_count(cls, value):
        if (value < 0) and (value > 7):
            raise ValueError('Value cannot be negative or > 7')
        return value

    child_mother_father_spouse_foreigner_count: int = 0

    @validator('child_mother_father_spouse_foreigner_count')
    def _child_mother_father_spouse_foreigner_count(cls, value):
        if (value < 0) and (value > 4 + 2 + 1):
            raise ValueError('Value cannot be negative or > 4 + 2 + 1')
        return value

    child_accompany: int = 0

    @validator('child_accompany')
    def _child_accompany(cls, value):
        if (value < 0) and (value > 4):
            raise ValueError('Value cannot be negative or > 4')
        return value

    parent_accompany: int = 0

    @validator('parent_accompany')
    def _parent_accompany(cls, value):
        if (value < 0) and (value > 2):
            raise ValueError('Value cannot be negative or > 2')
        return value

    spouse_accompany: int = 0

    @validator('spouse_accompany')
    def _spouse_accompany(cls, value):
        if (value < 0) and (value > 1):
            raise ValueError(
                'Value cannot be negative no matter how much u hate your spouse'
                ' Or bigger than one (having multiple spouse is a bad thing!)'
            )
        return value
    sibling_accompany: int = 0

    @validator('sibling_accompany')
    def _sibling_accompany(cls, value):
        if (value < 0) and (value > 7):
            raise ValueError('Value cannot be negative or > 7')
        return value

    child_average_age: float = 0.  # years

    child_count: int = 0

    @validator('child_count')
    def _child_count(cls, value):
        if (value < 0) and (value > 4):
            raise ValueError('Value cannot be negative or > 4')
        return value
    
    sibling_average_age: int = 0.

    sibling_count: int = 0

    @validator('sibling_count')
    def _sibling_count(cls, value):
        if (value < 0) and (value > 7):
            raise ValueError('Value cannot be negative or > 7')
        return value
    
    @validator(
        'child_average_age',
        'sibling_average_age',
    )
    def _child_sibling_average_period(cls, value):
        if value < 0:
            raise ValueError('Value cannot be negative')
        return value

    long_distance_child_sibling_count: int = 0

    @validator('long_distance_child_sibling_count')
    def _long_distance_child_sibling_count(cls, value):
        if (value < 0) and (value > 7 + 4):
            raise ValueError('Value cannot be negative or > 7 + 4')
        return value

    foreign_living_child_sibling_count: int = 0

    @validator('foreign_living_child_sibling_count')
    def _foreign_living_child_sibling_count(cls, value):
        if (value < 0) and (value > 7 + 4):
            raise ValueError('Value cannot be negative or > 7 + 4')
        return value

    class Config:
        orm_mode = True


class CanadaMarriageStatusResponse(BaseModel):
    """Canada marriage status states in string format

    Note:
        See :class:`cvfe.data.constant.CanadaMarriageStatus` for more info
        for possible values.
    """

    marriage_status_types: List[str]


class ChildRelationResponse(BaseModel):
    """Child relation types names

    Note:
        See :class:`cvfe.data.constant.ChildRelation` for more info
        for possible values.
    """

    child_relation_types: List[str]


class CanadaContactRelationResponse(BaseModel):
    """Contact relation types names in Canada

    Note:
        See :class:`cvfe.data.constant.CanadaContactRelation` for more info
        for possible values.
    """

    canada_contact_relation_types: List[str]


class CanadaResidencyStatusResponse(BaseModel):
    """Residency status types names in Canada

    Note:
        See :class:`cvfe.data.constant.CanadaResidencyStatus` for more info
        for possible values.
    """

    canada_residency_status_types: List[str]


class EducationFieldOfStudyResponse(BaseModel):
    """Education field of study types names

    Note:
        See :class:`cvfe.data.constant.EducationFieldOfStudy` for more info
        for possible values.
    """

    education_field_of_study_types: List[str]


class OccupationTitleResponse(BaseModel):
    """ Occupation title types names

    Note:
        See :class:`cvfe.data.constant.OccupationTitle` for more info
        for possible values.
    """

    occupation_title_types: List[str]


class XaiResponse(BaseModel):
    """XAI values for trained model

    Note:
        For more info about XAI and available methods, see :mod:`cvfe.xai.shap`. 
    
    """

    xai_overall_score: float
    xai_top_k: Dict[str, float]
    xai_txt_top_k: Dict[str, Tuple[float, str]]


class XaiFeatureCategoriesResponse(BaseModel):
    """Title of XAI categories
    
    Note:
        For example :dict:`cvfe.data.constant.FEATURE_CATEGORY_TO_FEATURE_NAME_MAP`
        contains the feature names for each category.
    """

    xai_feature_categories_types: List[str]


class XaiAggregatedGroupResponse(BaseModel):
    """XAI values grouped and aggregated into categories

    Note:
        This class :class:`cvfe.data.constant.FeatureCategories` contains the categories. 
        We use the names of the Enum items.
        For example, :dict:`cvfe.data.constant.FEATURE_CATEGORY_TO_FEATURE_NAME_MAP`
        contains the feature names for each categories.

    See Also:
        - XAI and available methods :mod:`cvfe.xai.shap`
        - XAI aggregation method :method:`cvfe.xai.shap.aggregate_shap_values`
    """

    aggregated_shap_values: Dict[str, float]
