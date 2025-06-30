import graphene
import re
from graphene_django import DjangoObjectType
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Customer

# Define DjangoObjectType for Customer model
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone", "created_at", "updated_at")

class CreateCustomer(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String(required=False)
        
    # Define output fields
    customer = graphene.Field(CustomerType)
    success = graphene.Boolean()
    message = graphene.String()
    errors = graphene.List(graphene.String)
    
    def mutate(self, info, name, email, phone=None):
        errors = []
        
        # Validate email uniqueness
        if Customer.objects.filter(email=email).exists():
            errors.append("A customer with this email already exists.")
        
        # Validate phone format if provided
        if phone:
            phone_pattern = r'^(\+[0-9]{1,3})?[0-9]{10}$|^[0-9]{3}-[0-9]{3}-[0-9]{4}$'
            if not re.match(phone_pattern, phone):
                errors.append("Phone number must be in the format: '+1234567890' or '123-456-7890'")
        
        if errors:
            return CreateCustomer(
                success=False,
                message="Validation failed.",
                errors=errors,
                customer=None
            )
        
        # Save customer to database
        try:
            customer = Customer(name=name, email=email, phone=phone)
            customer.full_clean()  # Model validation
            customer.save()
            return CreateCustomer(
                customer=customer,
                success=True,
                message="Customer created successfully.",
                errors=None
            )
        except ValidationError as e:
            errors = [str(error) for error in e.messages]
            return CreateCustomer(
                success=False,
                message="Validation failed.",
                errors=errors,
                customer=None
            )
        except Exception as e:
            return CreateCustomer(
                success=False,
                message="An error occurred while creating the customer.",
                errors=[str(e)],
                customer=None
            )


class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()