
import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth.models import User
from crm.schema import Query as CRMQuery, Mutation as CRMMutation

# class Query(graphene.ObjectType):
#     hello = graphene.String(default_value="Hello. GraphQL!")
    
# schema = graphene.Schema(query=Query)   
    
class Query(CRMQuery, graphene.ObjectType):
    pass
    
class Mutation(CRMMutation, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
