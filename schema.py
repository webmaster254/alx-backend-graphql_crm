
import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth.models import User

class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hello. GraphQL!")
    
schema = graphene.Schema(query=Query)   
    