
from django.utils import timezone
import graphene
from graphene_mongo import MongoengineObjectType
from graphene_django import DjangoObjectType
from .models import Test, Question, Option, User
import uuid

class UserType(DjangoObjectType):
    class Meta:
        model = User

class OptionType(MongoengineObjectType):
    class Meta:
        model = Option
    

class QuestionType(MongoengineObjectType):
    class Meta:
        model = Question
    options = graphene.List(OptionType)
    def resolve_options(self, info):
        # Return the actual Question documents related to this Test
        return self.options
        

class TestType(MongoengineObjectType):
    class Meta:
        model = Test  # Use the Mongoengine document  # Specify the fields to expose
        
    questions = graphene.List(QuestionType)
    def resolve_questions(self, info):
        # Return the actual Question documents related to this Test
        return self.questions

class Query(graphene.ObjectType):
    all_tests = graphene.List(TestType)
    def resolve_all_tests(root, info):
        return Test.objects.all()  # Returns all Test documents
    all_users = graphene.List(UserType)
    def resolve_all_users(root, info):
        return User.objects.all()  # Returns all Test documents

class CreateTestMutation(graphene.Mutation):
    class Arguments:
        test_name = graphene.String(required=True)
    test = graphene.Field(TestType)  # Return the created Test object
    
    def mutate(self, info, test_name):
        test = Test(test_name=test_name, test_id=str(uuid.uuid4()),
                    userid='a7c618c8-6ccb-401b-ac83-5846b86063b4', created=timezone.localtime(timezone.now()))
        test.save()
        return CreateTestMutation(test=test)

class Mutation(graphene.ObjectType):
        create_test = CreateTestMutation.Field()
        
schema = graphene.Schema(query=Query, mutation=Mutation)