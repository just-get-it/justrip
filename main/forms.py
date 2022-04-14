from django import forms
from django.db.models import fields
from .models import Charges, DriverProfile, Car, Fuel, Fuel_Route, Trip, TravellersInformation, CarType, OwnerProfile, CustomerProfile, VehicalCompany, VehicalGroup, VehicalType, CarCompany, VehicalName


def get_drivers():
    vendors = OwnerProfile.objects.filter(is_vendor=False)
    drivers = DriverProfile.objects.filter(owner__in=vendors)
    return drivers


class admin_owner_form(forms.Form):
    owner = forms.ModelChoiceField(
        queryset=OwnerProfile.objects.filter(is_verified=True, is_active=True))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['owner'].widget.attrs.update({'class': 'chosen-select'})


class admin_driver_form(forms.Form):
    driver = forms.ModelChoiceField(queryset=get_drivers())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['driver'].widget.attrs.update({'class': 'chosen-select'})


class driver_form(forms.ModelForm):
    class Meta():
        model = DriverProfile
        fields = (
            'name',
            'phone',
            'picture',
            'current_location',
            'aadhar_front_image',
            'aadhar_back_image',
            'aadhar_card_number',
            'police_verification',
            'driving_licence_front',
            'driving_licence_back',
            'driving_licence_number',
            'driving_licence_expiry_date',
            'taxi_badge_number'
        )
        labels = {
            'picture': 'Select Picture',
            'driving_licence_front': 'Select Licence Front Image',
            'driving_licence_back': 'Select Driving Licence Back Image',
            'aadhar_front_image': 'Select Aadhar Front Image',
            'aadhar_back_image': 'Select Aadhar Back Image',
            'police_verification': 'Select Police Verification Document Image'
        }
        widgets = {
            'driving_licence_expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'phone': forms.NumberInput(attrs={'maxlength': '10'}),
            'aadhar_card_number': forms.NumberInput(attrs={'maxlength': '14'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['picture'].widget.attrs.update(
            {'onchange': 'ImgDisplay(this, "picture_display")'})
        self.fields['driving_licence_front'].widget.attrs.update(
            {'onchange': 'ImgDisplay(this, "driving_licence_front_display")'})
        self.fields['driving_licence_back'].widget.attrs.update(
            {'onchange': 'ImgDisplay(this, "driving_licence_back_display")'})
        self.fields['aadhar_front_image'].widget.attrs.update(
            {'onchange': 'ImgDisplay(this, "aadhar_front_image_display")'})
        self.fields['aadhar_back_image'].widget.attrs.update(
            {'onchange': 'ImgDisplay(this, "aadhar_back_image_display")'})
        self.fields['police_verification'].widget.attrs.update(
            {'onchange': 'ImgDisplay(this, "police_verification_image_display")'})


class owner_state_form(forms.ModelForm):
    class Meta():
        model = OwnerProfile
        fields = ('states',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['states'].widget.attrs.update({'class': 'chosen-select'})


class car_form(forms.ModelForm):
    class Meta():
        model = Car
        fields = ('type', 'company', 'name', 'licence_plate_no', 'rc_book_front', 'rc_book_back', 'car_year', 'owner_name', 'rc_book_expiry_date',
                  'chassi_number', 'insurance_no', 'insurance_picture', 'insurance_expiry_date', 'insurance_company', 'fitness_certificate',
                  'fitness_expiry_date', 'cab_noc_agreement',
                  'car_front', 'car_back', 'car_side_left', 'car_side_right', 'car_interior_front', 'car_interior_back', 'car_dickie')
        labels = {
            'cab_noc_agreement': 'Cab NOC agreement',
            'insurance_picture': 'Select Insurance Picture',
            'rc_book_front': 'Select RC Book Front Picture',
            'rc_book_back': 'Select RC Book Back Picture',
            'fitness_certificate': 'Select Car Fitness Certificate Image',
            'car_front': 'Select Car Front Image',
            'car_back': 'Select Car Back Image',
            'car_side_left': 'Select Car Side Left Image',
            'car_side_right': 'Select Side Right Image',
            'car_interior_front': 'Select Car Interior Front Image',
            'car_interior_back': 'Select Car Interior Back Image',
            'car_dickie': 'Select Car Dickie Image',
        }
        widgets = {
            'insurance_expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'rc_book_expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'insurance_no': forms.NumberInput(),
            'fitness_expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['insurance_picture'].widget.attrs.update(
            {'onchange': 'ImgDisplay(this, "insurance_picture_display")'})
        self.fields['rc_book_front'].widget.attrs.update(
            {'onchange': 'ImgDisplay(this, "rc_book_front_display")'})
        self.fields['rc_book_back'].widget.attrs.update(
            {'onchange': 'ImgDisplay(this, "rc_book_back_display")'})
        self.fields['fitness_certificate'].widget.attrs.update(
            {'onchange': 'ImgDisplay(this, "fitness_certificate_display")'})
        self.fields['car_front'].widget.attrs.update(
            {'onchange': 'ImgDisplay(this, "car_front_display")'})
        self.fields['car_back'].widget.attrs.update(
            {'onchange': 'ImgDisplay(this, "car_back_display")'})
        self.fields['car_side_left'].widget.attrs.update(
            {'onchange': 'ImgDisplay(this, "car_side_left_display")'})
        self.fields['car_side_right'].widget.attrs.update(
            {'onchange': 'ImgDisplay(this, "car_side_right_display")'})
        self.fields['car_interior_front'].widget.attrs.update(
            {'onchange': 'ImgDisplay(this, "car_interior_front_display")'})
        self.fields['car_interior_back'].widget.attrs.update(
            {'onchange': 'ImgDisplay(this, "car_interior_back_display")'})
        self.fields['car_dickie'].widget.attrs.update(
            {'onchange': 'ImgDisplay(this, "car_dickie_display")'})
        self.fields['cab_noc_agreement'].widget.attrs.update(
            {'onchange': 'ImgDisplay(this, "cab_noc_agreement_display")'})


class trip_pickup(forms.ModelForm):
    class Meta():
        model = Trip
        fields = ('pickup_location',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pickup_location'].widget.attrs.update(
            {'style': 'height: auto; display:none;', 'required': 'required'})


class trip(forms.ModelForm):
    class Meta():
        model = Trip
        fields = ('trip_type', 'trip_variant', 'trip_way',
                  'pickup_location', 'drop_location')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pickup_location'].widget.attrs.update(
            {'style': 'height: auto; ', 'required': 'required'})
        self.fields['drop_location'].widget.attrs.update(
            {'style': 'height: auto; ', 'required': 'required'})


class trip_selection_form(forms.ModelForm):
    class Meta():
        model = Charges
        fields = ('trip_type', 'trip_variant', 'trip_way')


class trip_drop(forms.ModelForm):
    class Meta():
        model = Trip
        fields = ('pickup_location', 'drop_location',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['drop_location'].widget.attrs.update(
            {'style': 'height: auto; display:none;', 'required': 'required'})
        self.fields['pickup_location'].widget = forms.HiddenInput()


class trip_final_form(forms.ModelForm):
    # round_trip = forms.ChoiceField(choices=[('False','One Way Trip'),('True','Round Trip')], widget=forms.RadioSelect(attrs={'onchange':'get_cost()'}))
    # round_trip = forms.HiddenInput()
    class Meta():
        model = Trip
        fields = ('car_type', 'pickup_location', 'drop_location', 'round_trip', 'distance', 'trip_perimeter')
      
        widgets = {
            # 'round_trip': forms.CheckboxInput(),
            # 'drop_location': forms.HiddenInput(),
            # 'pickup_location': forms.HiddenInput(),
            # 'distance': forms.HiddenInput(),
            # 'pickup_time': forms.TextInput(attrs={'type':'datetime-local', 'class':'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['round_trip'].widget = forms.CheckboxInput()
        self.fields['trip_perimeter'].widget = forms.CheckboxInput()
        self.fields['drop_location'].widget = forms.HiddenInput()
        self.fields['pickup_location'].widget = forms.HiddenInput()
        self.fields['distance'].widget = forms.HiddenInput()
        # self.fields['pickup_time'].widget.attrs = {'type':'datetime-local', 'class':'form-control'}
        self.fields['car_type'].widget.attrs.update(
            {'class': 'form-control', 'onchange': 'get_cost()'})
        # self.fields['round_trip'].widget.attrs.update({'onchange':'get_cost()'})


class traveller_form(forms.ModelForm):
    phone = forms.RegexField(regex=r'^\+?1?\d{10,12}$')

    class Meta():
        model = TravellersInformation
        exclude = ('trip',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'class': 'form-control'})
        self.fields['phone'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['address'].widget.attrs.update({'class': 'form-control'})
        self.fields['no_of_travellers'].widget.attrs.update(
            {'class': 'form-control'})
        self.fields['no_of_bags'].widget.attrs.update(
            {'class': 'form-control'})
        self.fields['special_instructions'].widget.attrs.update(
            {'class': 'form-control'})


class owner_address_form(forms.ModelForm):
    class Meta():
        model = OwnerProfile
        fields = ('address_coords',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['address_coords'].widget.attrs.update(
            {'style': 'height: auto; display: none;'})


class customer_address_form(forms.ModelForm):
    class Meta():
        model = CustomerProfile
        fields = ('address',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['address'].widget.attrs.update(
            {'style': 'height: auto; display: none;'})


class car_type_form(forms.ModelForm):
    class Meta():
        model = CarType
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['picture'].widget.attrs.update(
            {'onchange': 'ImgDisplay(this, "car_type_image_display")', 'value': 'true'})


class VehicalNameForm(forms.ModelForm):
    class Meta:
        model = VehicalName
        fields = ('__all__')

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     # print(self)
    #     # self.fields['type'].queryset = VehicalType.objects.none()

    #     try:
    #         group_id = self.initial['group']
    #         # print(group_id)
    #         self.fields['type'].queryset = VehicalType.objects.filter(group=group_id).order_by('name')
    #         self.fields['company'].queryset = CarCompany.objects.filter(group=group_id).order_by('name')
    #     except (ValueError, TypeError):
    #         print("error occured")  # invalid input from the client; ignore and fallback to empty City queryset


class VehicalComapnyForm(forms.ModelForm):
    class Meta:
        model = VehicalCompany
        fields = ('__all__')
class VehicalNameForm(forms.ModelForm):
    class Meta:
        model = VehicalName
        fields = ('__all__')


class FuelRouteForm(forms.ModelForm):
    fuel_type = forms.ModelMultipleChoiceField(
        queryset=Fuel.objects, widget=forms.CheckboxSelectMultiple())

    class meta:
        model = Fuel_Route
        fields = ('__all__')
