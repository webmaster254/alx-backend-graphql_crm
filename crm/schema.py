import graphene
import re
from graphene_django import DjangoObjectType
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Customer, Product, Order

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
            phone_pattern = r'^(\+\d{1,4}\d{7,14}|\d{3}-\d{3}-\d{4})$'
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



  
        
# Input type for customer data
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=False)


# Result type for bulk creation results
class BulkCreateCustomerResult(graphene.ObjectType):
    customer = graphene.Field(CustomerType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        customers = graphene.List(CustomerInput, required=True)

    # Output fields
    success_count = graphene.Int()
    failed_count = graphene.Int()
    results = graphene.List(BulkCreateCustomerResult)

    def mutate(self, info, customers):
        results = []
        success_count = 0
        failed_count = 0

        # Use a transaction.atomic block to ensure data integrity
        from django.db import transaction
        
        # List to track emails for duplicate checking within this batch
        batch_emails = set()

        # First validation pass - validate all customers
        validated_customers = []
        for customer_data in customers:
            errors = []
            name = customer_data.name
            email = customer_data.email
            phone = customer_data.phone if hasattr(customer_data, 'phone') else None
            
            # Check for duplicate emails in database
            if Customer.objects.filter(email=email).exists():
                errors.append(f"Customer with email '{email}' already exists in database.")
            
            # Check for duplicate emails within this batch submission
            elif email in batch_emails:
                errors.append(f"Duplicate email '{email}' in submission batch.")
            else:
                batch_emails.add(email)
            
            # Validate phone format
            if phone:
                phone_pattern = r'^(\+\d{1,4}\d{7,14}|\d{3}-\d{3}-\d{4})$'
                if not re.match(phone_pattern, phone):
                    errors.append(f"Invalid phone format for '{email}'. Must be in format: '+1234567890' or '123-456-7890'")
            
            if errors:
                results.append(BulkCreateCustomerResult(
                    customer=None,
                    success=False,
                    errors=errors
                ))
                failed_count += 1
            else:
                validated_customers.append((name, email, phone))
        
        # Begin atomic transaction for creating valid customers
        with transaction.atomic():
            # Second pass - create customers for valid entries
            for name, email, phone in validated_customers:
                try:
                    customer = Customer(name=name, email=email, phone=phone)
                    customer.full_clean()
                    customer.save()
                    results.append(BulkCreateCustomerResult(
                        customer=customer,
                        success=True,
                        errors=None
                    ))
                    success_count += 1
                except ValidationError as e:
                    error_messages = [str(error) for error in e.messages] 
                    results.append(BulkCreateCustomerResult(
                        customer=None,
                        success=False,
                        errors=error_messages
                    ))
                    failed_count += 1
                except Exception as e:
                    results.append(BulkCreateCustomerResult(
                        customer=None,
                        success=False,
                        errors=[str(e)]
                    ))
                    failed_count += 1
        
        return BulkCreateCustomers(
            success_count=success_count,
            failed_count=failed_count,
            results=results
        )

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock",  "created_at", "updated_at")


class CreatProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Decimal(required=True)
        stock = graphene.Int(required=True)
        
    product = graphene.Field(ProductType)
    success = graphene.Boolean()
    message = graphene.String()
    errors = graphene.List(graphene.String)
    
    def mutate(self, info, name, price, stock):
        errors = []
        
        # Validate price
        if price < 0:
            errors.append("Price must be a positive number.")
        
        if errors:
            return CreatProduct(
                product=None,
                success=False,
                message="Validation failed.",
                errors=errors
            )
        
        # Save product to database
        try:
            product = Product(name=name, price=price, stock=stock)
            product.full_clean()  # Model validation
            product.save()
            return CreatProduct(
                product=product,
                success=True,
                message="Product created successfully.",
                errors=None
            )
        except ValidationError as e:
            errors = [str(error) for error in e.messages]
            return CreatProduct(
                product=None,
                success=False,
                message="Validation failed.",
                errors=errors
            )
        except Exception as e:
            return CreatProduct(
                product=None,
                success=False,
                message="An error occurred while creating the product.",
                errors=[str(e)]
            )


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "customer", "product", "order_date", "total_sum", "created_at", "updated_at")

class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.Int(required=True)
        product_ids = graphene.List(graphene.Int, required=True)
        order_date = graphene.DateTime(required=False)
    
    order = graphene.Field(OrderType)
    success = graphene.Boolean()
    message = graphene.String()
    errors = graphene.List(graphene.String)
    
    def mutate(self, info, customer_id, product_ids, order_date=None):
        errors = []
        
        # Validate customer existence
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            errors.append(f"Customer with ID {customer_id} not found.")
            return CreateOrder(
                order=None,
                success=False,
                message="Customer validation failed.",
                errors=errors
            )
        
        # Validate at least one product is selected
        if not product_ids:
            errors.append("At least one product must be selected.")
            return CreateOrder(
                order=None,
                success=False,
                message="Product validation failed.",
                errors=errors
            )
        
        # Validate products existence
        products = Product.objects.filter(id__in=product_ids)
        if products.count() != len(product_ids):
            # Find which product IDs don't exist
            found_ids = set(products.values_list('id', flat=True))
            missing_ids = [pid for pid in product_ids if pid not in found_ids]
            for pid in missing_ids:
                errors.append(f"Product with ID {pid} not found.")
            
            return CreateOrder(
                order=None,
                success=False,
                message="Product validation failed.",
                errors=errors
            )
        
        # Calculate total amount as the sum of product prices
        total_amount = sum(product.price for product in products)
        
        # Create order and order items in a transaction
        from django.db import transaction
        
        try:
            with transaction.atomic():
                # Create the main order
                order = Order(
                    customer=customer,
                    total_sum=total_amount
                )
                
                # Set order_date if provided
                if order_date:
                    order.order_date = order_date
                    
                order.full_clean()
                order.save()
                
                # Create the order items
                for product in products:
                    order_item = OrderItem(
                        order=order,
                        product=product,
                        quantity=1,  # Default quantity of 1 per product
                        item_total=product.price
                    )
                    order_item.full_clean()
                    order_item.save()
                
            return CreateOrder(
                order=order,
                success=True,
                message="Order created successfully.",
                errors=None
            )
        except ValidationError as e:
            if hasattr(e, 'error_dict'):
                errors = [str(e.error_dict[field][0]) for field in e.error_dict]
            else:
                errors = [str(error) for error in e.messages]
            return CreateOrder(
                order=None,
                success=False,
                message="Validation failed.",
                errors=errors
            )
        except Exception as e:
            return CreateOrder(
                order=None,
                success=False,
                message="An error occurred while creating the order.",
                errors=[str(e)]
            )
            
            
class Query(graphene.ObjectType):
    customers = graphene.List(CustomerType)
    products = graphene.List(ProductType)
    orders = graphene.List(OrderType)
    
    def resolve_customers(self, info):
        return Customer.objects.all()
    
    def resolve_products(self, info):
        return Product.objects.all()
    
    def resolve_orders(self, info):
        return Order.objects.all()
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreatProduct.Field()
    create_order = CreateOrder.Field()