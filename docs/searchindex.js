Search.setIndex({docnames:["clients","developing","index","providers","quickstart"],envversion:{"sphinx.domains.c":2,"sphinx.domains.changeset":1,"sphinx.domains.citation":1,"sphinx.domains.cpp":3,"sphinx.domains.index":1,"sphinx.domains.javascript":2,"sphinx.domains.math":2,"sphinx.domains.python":2,"sphinx.domains.rst":2,"sphinx.domains.std":2,sphinx:56},filenames:["clients.rst","developing.rst","index.rst","providers.rst","quickstart.rst"],objects:{"keydra.clients":{bitbucket:[0,0,0,"-"],cloudflare:[0,0,0,"-"],contentful:[0,0,0,"-"],qualys:[0,0,0,"-"],salesforce:[0,0,0,"-"],splunk:[0,0,0,"-"]},"keydra.clients.aws":{appsync:[0,0,0,"-"],secretsmanager:[0,0,0,"-"]},"keydra.clients.aws.appsync":{AppSyncClient:[0,1,1,""],CreateApiKeyException:[0,3,1,""],DeleteApiKeyException:[0,3,1,""],GetApiException:[0,3,1,""],ListApiKeysException:[0,3,1,""]},"keydra.clients.aws.appsync.AppSyncClient":{create_api_key:[0,2,1,""],delete_api_key:[0,2,1,""],get_graphql_api:[0,2,1,""],list_api_keys:[0,2,1,""]},"keydra.clients.aws.secretsmanager":{GetSecretException:[0,3,1,""],InsertSecretException:[0,3,1,""],SecretsManagerClient:[0,1,1,""],UpdateSecretException:[0,3,1,""]},"keydra.clients.aws.secretsmanager.SecretsManagerClient":{create_secret:[0,2,1,""],describe_secret:[0,2,1,""],generate_random_password:[0,2,1,""],get_secret_value:[0,2,1,""],update_secret:[0,2,1,""],update_secret_description:[0,2,1,""]},"keydra.clients.bitbucket":{BitbucketClient:[0,1,1,""]},"keydra.clients.bitbucket.BitbucketClient":{_delete:[0,2,1,""],_fetch_all:[0,2,1,""],_post:[0,2,1,""],_put:[0,2,1,""],_query:[0,2,1,""],add_repo_deployment_variable:[0,2,1,""],add_repo_environment:[0,2,1,""],add_repo_variable:[0,2,1,""],add_team_pipeline_variable:[0,2,1,""],delete_team_pipeline_variable:[0,2,1,""],fetch_file_from_repository:[0,2,1,""],list_repo_deployment_variables:[0,2,1,""],list_repo_environments:[0,2,1,""],list_repo_variables:[0,2,1,""],list_team_pipeline_variables:[0,2,1,""],update_repo_deployment_variable:[0,2,1,""],update_repo_variable:[0,2,1,""],update_team_pipeline_variable:[0,2,1,""]},"keydra.clients.cloudflare":{CloudflareClient:[0,1,1,""]},"keydra.clients.cloudflare.CloudflareClient":{_delete:[0,2,1,""],_post:[0,2,1,""],_put:[0,2,1,""],_query:[0,2,1,""],details:[0,2,1,""],list_tokens:[0,2,1,""],roll_token:[0,2,1,""],verify:[0,2,1,""]},"keydra.clients.contentful":{ConnectionException:[0,3,1,""],ContentfulClient:[0,1,1,""],ParameterException:[0,3,1,""]},"keydra.clients.contentful.ContentfulClient":{_validate_client:[0,2,1,""],create_token:[0,2,1,""],get_tokens:[0,2,1,""],revoke_token:[0,2,1,""]},"keydra.clients.qualys":{ConnectionException:[0,3,1,""],PasswordChangeException:[0,3,1,""],QualysClient:[0,1,1,""]},"keydra.clients.qualys.QualysClient":{_get:[0,2,1,""],_user_list:[0,2,1,""],change_passwd:[0,2,1,""]},"keydra.clients.salesforce":{SalesforceClient:[0,1,1,""],ValidationException:[0,3,1,""]},"keydra.clients.salesforce.SalesforceClient":{change_passwd:[0,2,1,""],get_user_id:[0,2,1,""]},"keydra.clients.splunk":{AppNotInstalledException:[0,3,1,""],SplunkClient:[0,1,1,""]},"keydra.clients.splunk.SplunkClient":{app_exists:[0,2,1,""],change_passwd:[0,2,1,""],update_app_config:[0,2,1,""]},"keydra.providers":{aws_appsync:[3,0,0,"-"],aws_iam:[3,0,0,"-"],aws_secretsmanager:[3,0,0,"-"],bitbucket:[3,0,0,"-"],cloudflare:[3,0,0,"-"],contentful:[3,0,0,"-"],qualys:[3,0,0,"-"],salesforce:[3,0,0,"-"],splunk:[3,0,0,"-"]},"keydra.providers.aws_appsync":{Client:[3,1,1,""]},"keydra.providers.aws_appsync.Client":{_abc_impl:[3,4,1,""],_generate_expiry_epoch:[3,2,1,""],_get_days_from_occurrence:[3,2,1,""],_rotate:[3,2,1,""],distribute:[3,2,1,""],redact_result:[3,2,1,""],rotate:[3,2,1,""],validate_spec:[3,2,1,""]},"keydra.providers.aws_iam":{Client:[3,1,1,""],_explain_secret:[3,5,1,""]},"keydra.providers.aws_iam.Client":{_abc_impl:[3,4,1,""],_create_access_key:[3,2,1,""],_create_user_if_not_available:[3,2,1,""],_delete_access_key:[3,2,1,""],_fetch_access_keys:[3,2,1,""],_pick_best_candidate:[3,2,1,""],_update_access_key:[3,2,1,""],_update_user_group_membership:[3,2,1,""],distribute:[3,2,1,""],redact_result:[3,2,1,""],rotate:[3,2,1,""],validate_spec:[3,2,1,""]},"keydra.providers.aws_secretsmanager":{SecretsManagerProvider:[3,1,1,""]},"keydra.providers.aws_secretsmanager.SecretsManagerProvider":{Options:[3,1,1,""],_abc_impl:[3,4,1,""],_distribute_secret:[3,2,1,""],_generate_secret_value:[3,2,1,""],_get_current_secret:[3,2,1,""],distribute:[3,2,1,""],redact_result:[3,2,1,""],rotate:[3,2,1,""],validate_spec:[3,2,1,""]},"keydra.providers.aws_secretsmanager.SecretsManagerProvider.Options":{_asdict:[3,2,1,""],_field_defaults:[3,4,1,""],_field_types:[3,4,1,""],_fields:[3,4,1,""],_fields_defaults:[3,4,1,""],_make:[3,2,1,""],_replace:[3,2,1,""],bypass:[3,4,1,""],exclude_char:[3,4,1,""],exclude_lower:[3,4,1,""],exclude_num:[3,4,1,""],exclude_punct:[3,4,1,""],exclude_upper:[3,4,1,""],include_space:[3,4,1,""],length:[3,4,1,""],require_each_type:[3,4,1,""],rotate_attribute:[3,4,1,""]},"keydra.providers.bitbucket":{Client:[3,1,1,""]},"keydra.providers.bitbucket.Client":{_abc_impl:[3,4,1,""],_distribute:[3,2,1,""],_distribute_account_secret:[3,2,1,""],_distribute_deployment_secret:[3,2,1,""],_distribute_repository_secret:[3,2,1,""],_get_or_create_environment:[3,2,1,""],_load_remote_file:[3,2,1,""],_validate_deployment_spec:[3,2,1,""],_validate_repository_spec:[3,2,1,""],distribute:[3,2,1,""],load_config:[3,2,1,""],pre_process_spec:[3,2,1,""],rotate:[3,2,1,""],validate_spec:[3,2,1,""]},"keydra.providers.cloudflare":{Client:[3,1,1,""],CloudflareException:[3,3,1,""]},"keydra.providers.cloudflare.Client":{_abc_impl:[3,4,1,""],_rotate:[3,2,1,""],distribute:[3,2,1,""],redact_result:[3,2,1,""],rotate:[3,2,1,""]},"keydra.providers.contentful":{Client:[3,1,1,""]},"keydra.providers.contentful.Client":{_abc_impl:[3,4,1,""],_rotate_secret:[3,2,1,""],distribute:[3,2,1,""],redact_result:[3,2,1,""],rotate:[3,2,1,""]},"keydra.providers.qualys":{Client:[3,1,1,""]},"keydra.providers.qualys.Client":{_abc_impl:[3,4,1,""],_rotate_secret:[3,2,1,""],distribute:[3,2,1,""],redact_result:[3,2,1,""],rotate:[3,2,1,""],validate_spec:[3,2,1,""]},"keydra.providers.salesforce":{Client:[3,1,1,""]},"keydra.providers.salesforce.Client":{_abc_impl:[3,4,1,""],_generate_sforce_passwd:[3,2,1,""],_rotate_secret:[3,2,1,""],distribute:[3,2,1,""],redact_result:[3,2,1,""],rotate:[3,2,1,""],validate_spec:[3,2,1,""]},"keydra.providers.splunk":{Client:[3,1,1,""]},"keydra.providers.splunk.Client":{_abc_impl:[3,4,1,""],_distribute:[3,2,1,""],_generate_splunk_passwd:[3,2,1,""],_rotate_secret:[3,2,1,""],distribute:[3,2,1,""],redact_result:[3,2,1,""],rotate:[3,2,1,""],validate_spec:[3,2,1,""]}},objnames:{"0":["py","module","Python module"],"1":["py","class","Python class"],"2":["py","method","Python method"],"3":["py","exception","Python exception"],"4":["py","attribute","Python attribute"],"5":["py","function","Python function"]},objtypes:{"0":"py:module","1":"py:class","2":"py:method","3":"py:exception","4":"py:attribute","5":"py:function"},terms:{"123":0,"8089":0,"case":[2,4],"class":[0,3],"default":[0,4],"function":[2,3,4],"int":[0,3],"new":[0,1,2,3,4],"return":[0,1,3],"true":[0,3,4],AWS:2,BUT:1,But:1,For:[2,3,4],The:[0,1,3,4],Then:3,These:2,Use:2,Uses:3,Will:0,With:[3,4],_abc_data:3,_abc_impl:3,_asdict:3,_commonly_:1,_create_access_kei:3,_create_user_if_not_avail:3,_delet:0,_delete_access_kei:3,_distribut:3,_distribute_:1,_distribute_account_secret:3,_distribute_deployment_secret:3,_distribute_repository_secret:3,_distribute_secret:3,_explain_secret:3,_fetch_access_kei:3,_fetch_al:0,_field:3,_field_default:3,_field_typ:3,_fields_default:3,_generate_expiry_epoch:3,_generate_secret_valu:3,_generate_sforce_passwd:3,_generate_splunk_passwd:3,_get:0,_get_current_secret:3,_get_days_from_occurr:3,_get_or_create_environ:3,_greedy_:3,_load_remote_fil:3,_make:3,_pick_best_candid:3,_post:0,_put:0,_queri:0,_replac:3,_rotat:3,_rotate_:1,_rotate_secret:3,_update_access_kei:3,_update_user_group_membership:3,_user_list:0,_validate_cli:0,_validate_deployment_spec:3,_validate_repository_spec:3,about:[0,1,4],access:[0,3,4],account:[0,2,3,4],account_usernam:4,activ:[3,4],add:[0,4],add_repo_deployment_vari:0,add_repo_environ:0,add_repo_vari:0,add_team_pipeline_vari:0,added:[0,3],adding:1,addit:0,additionalauthenticationprovid:0,address:0,adhoc:4,admin:[0,4],admin_lock:0,after:[0,4],against:2,alia:3,all:[0,1,2,3,4],allow:[0,2],alreadi:0,also:[1,3,4],alwai:4,amazon:4,angl:4,ani:[0,3],anoth:4,anywai:1,api:[0,2,3],api_id:0,api_kei:0,apiid:0,apikei:0,apius:3,app:[0,3,4],app_exist:0,append:4,appidclientregex:0,appnam:0,appnotinstalledexcept:0,appsynccli:0,arn:[0,4],ask:1,aspir:1,assum:4,athena:4,atlassian:4,attach:0,attack:2,attribut:1,authenticationtyp:0,authttl:0,auto:4,autom:2,automag:4,automat:2,automaticallyafterdai:0,avail:[0,3],avatar:4,aws:[0,3,4],aws_access_key_id:4,aws_appsync:3,aws_iam:3,aws_secret:3,aws_secret_access_kei:4,aws_secretsmanag:3,awscurr:0,awsprevi:0,awsregion:0,backup:3,base:[0,1],been:3,befor:[1,3],begin:1,being:4,below:1,best:4,bit:[0,1],bitbucket:[2,4],bitbucketcli:0,block:4,blue:4,bool:[0,3],both:1,boto:0,bottom:4,box:1,bracket:4,branch:1,brought:1,brows:4,build:[3,4],button:4,bypass:[0,3],call:[2,4],can:[1,3,4],capability_auto_expand:4,capability_iam:4,capability_named_iam:4,capabl:4,certain:1,chanc:1,chang:[0,2,3,4],change_passwd:0,check:[0,2],cherri:3,choos:4,classmethod:3,clean:1,click:4,client:3,clientid:0,clone:4,cloudflarecli:0,cloudflareexcept:3,cloudform:4,cloudwatchlogsrolearn:0,code:[0,1,4],com:[3,4],come:1,commit:4,complex:0,compliant:[0,1],compromis:[2,4],config:[0,1,3,4],configur:[0,3],conjunct:3,connect:[0,3,4],connectionexcept:0,consol:4,consum:1,contain:[1,4],contentful_manag:0,contentfulcli:0,context:[0,3],copi:4,corner:4,correspond:0,could:4,coverag:1,creat:[0,1,3,4],create_api_kei:0,create_secret:0,create_token:0,createapikeyexcept:0,cred:3,credenti:[2,3,4],current:[0,2,3],custodian:4,cut:1,dai:2,dark:4,data:0,datetim:0,daunt:4,days_from_todai:3,debug:4,declar:3,decor:1,decreas:2,defaultact:0,defin:[2,4],definit:4,delet:0,delete_api_kei:0,delete_team_pipeline_vari:0,deleteapikeyexcept:0,deletedd:0,deni:0,dep:1,depend:[1,4],deploy:[0,2,3],describ:[0,1],describe_secret:0,descript:[0,1,3,4],dest:3,destin:3,detail:[0,1,4],dev:[1,4],develop:[3,4],dict:[0,1,3],dictionari:0,dictonari:0,did:1,directli:1,directori:4,discuss:1,distribut:[2,3,4],doc:4,docker:4,document:1,doe:[0,3],doesn:[0,3],domain:0,don:[1,4],done:[2,3],down:4,drop:1,dure:1,each:2,easi:[2,4],edit:4,els:1,email:0,enabl:4,encrypt:0,encypt:4,ensur:[1,4],entri:0,env:[0,3,4],env_typ:0,env_uuid:0,enviro:4,environ:[0,3,4],error:0,event:4,everi:[0,4],everydai:2,everyth:4,exampl:[1,2,3,4],except:[0,1,3],exclude_char:3,exclude_low:3,exclude_num:3,exclude_punct:3,exclude_upp:3,excludecharact:0,excludelowercas:0,excludenumb:0,excludepunctu:0,excludeuppercas:0,excludeverbosecont:0,execut:4,exist:[0,3,4],expect:4,expir:0,explanatori:1,expos:4,facilit:1,fals:[0,3],fast:1,featur:1,fetch:[0,3],fetch_file_from_repositori:0,field:[0,3],fieldloglevel:0,file:[0,4],filetyp:3,fine:4,first:4,flake8:1,follow:[3,4],form:0,format:[3,4],fragment:3,free:4,frequent:[2,4],friend:4,friendli:0,from:[0,1,2,3,4],full:0,futur:[3,4],gener:[0,3],generate_random_password:0,get:0,get_graphql_api:0,get_secret_valu:0,get_token:0,get_user_id:0,getapiexcept:0,getsecretexcept:0,git:4,github:4,give:4,given:[0,3],goe:1,going:[0,1,4],graphqlapi:0,group:[3,4],grow:2,happen:[1,4],hardcod:4,has:[1,2,3],have:[0,1,4],help:4,here:[1,3,4],hidden:0,home:4,host:[0,4],how:[0,1,4],http:[0,3,4],human:[0,4],iam:[2,4],iam_us:3,iatttl:0,identif:3,identifi:[0,3],impact:4,implement:[1,3],includ:[0,1],include_spac:3,includespac:0,inform:0,initialis:4,insertsecretexcept:0,instal:[1,4],instanc:3,integr:2,invok:[1,3],issuer:0,iter:3,its:3,itself:4,json:[0,4],judgement:1,just:[1,4],keep:1,kei:[0,1,2,3,4],key_id:3,key_identifi:1,keydra:[0,3],keydra_deploi:4,keydra_managed_sampl:4,keydraconfigur:4,keydradeploi:4,keydraexecrol:4,keys_by_id:3,kindli:4,kmskeyid:0,kwarg:[0,3],kwd:3,label:0,lambda:[2,4],lamnda:4,lastaccessedd:0,lastchangedd:0,lastrotatedd:0,least:[0,4],leav:4,left:4,length:[0,3],let:4,level:[0,2,3],like:[1,2,4],limit:4,line:4,list:[0,2,3],list_api_kei:0,list_repo_deployment_vari:0,list_repo_environ:0,list_repo_vari:0,list_team_pipeline_vari:0,list_token:0,listapikeysexcept:0,littl:4,live:1,load_config:3,loan:4,local:4,locat:3,lock:0,log:1,logconfig:0,login:4,look:4,lookup:0,lot:4,lower:[2,4],luck:4,machin:4,magic:1,mai:[1,4],main:[2,4],make:[1,3,4],manag:4,manage_token:3,managedbi:4,manual:3,map:3,match:[0,4],mean:1,mess:1,method:1,minimum:4,minu:0,miss:1,mkdir:4,modular:2,moment:1,more:[1,2],much:2,multipl:2,my_team:4,mydeploymentgroup:4,name:[0,3,4],navig:4,need:[1,3],never:1,newli:0,newpasswd:0,newpassword:0,next:[2,4],nexttoken:0,nice:4,night:4,nightli:[1,3,4],none:[0,3],nonetyp:3,nosetest:1,note:[0,1,3,4],noth:1,now:4,number:3,obj:0,object:[0,3],occurr:3,oldpasswd:0,onc:[2,4],one:[0,3,4],onli:[0,3,4],onto:4,open:4,openidconnectconfig:0,oper:0,opt:3,option:[0,3],orang:4,ordereddict:0,org:4,organis:2,origin:4,other:[1,3,4],otherwis:0,our:4,out:[1,2],output:4,own:3,owningservic:0,page:[0,4],param:0,paramet:[0,3],parameterexcept:0,pass:1,passwd:[0,3],password:[0,1,2,3,4],passwordchangeexcept:0,past:4,path:[0,3,4],pep8:1,per:[0,3],period:2,permiss:[3,4],permit:3,person:[0,4],personal_access_token:0,personalaccesstoken:0,pertain:3,phase:1,pick:3,pip:[1,4],pipelin:[2,4],place:3,plain:1,plaintext:4,platform:[0,2,3],pleas:[1,3],point:1,polici:4,popul:0,port:0,post:0,pre_process_spec:3,previou:0,price:2,privat:4,privileg:[0,4],probabl:1,prod:3,product:[0,4],programmat:4,provid:[0,2,4],provider_typ:1,provis:1,pull:1,purpos:[0,3],push:4,put:4,python:4,qualyscli:0,queri:0,rais:[0,1],random:[0,3],randomli:0,rather:4,read:0,readi:[1,3],readonli:0,realli:[1,3],receiv:[1,3],recent:1,redact_result:3,region:4,region_nam:[0,3],regist:3,rememb:1,replac:[2,3],repo:[0,3,4],repo_slug:0,repositori:[0,2,3],request:[0,1],requir:[0,1,3,4],require_each_typ:3,requireeachincludedtyp:0,respect:3,respons:[0,1],result:[0,3,4],retriev:[0,3],reveal:0,revok:0,revoke_token:0,right:4,risk:2,role:4,roll:0,roll_token:0,rotat:[0,2,3,4],rotate_attribut:3,rotatewith:3,rotationen:0,rotationexcept:1,rotationlambdaarn:0,rotationrul:0,run:2,safe:1,salesforc:2,salesforcecli:0,sam:4,same:4,sampl:[0,3,4],sample_templ:4,schedul:2,scope:[3,4],screen:4,scroll:4,sdk:1,second:[3,4],secret:[1,4],secret_id:0,secret_identifi:1,secret_kei:3,secret_nam:0,secret_valu:0,secretsmanag:[0,2,3],secretsmanagercli:[0,3],secretsmanagerprovid:3,section:4,secur:0,see:[1,3,4],seen:4,select:4,self:1,sell:4,send:0,sens:3,separ:4,sequenc:3,server:3,serverless:4,servic:[2,4],session:[0,3],set:4,setup:3,should:[0,1,3,4],shown:4,significanti:2,simpl:1,simpli:1,sinc:2,singl:[0,2],slug:0,sneaki:4,some:1,someth:[1,4],somewher:1,soon:4,sourc:[1,3,4],southeast:4,space:0,spec:[0,3],specif:[0,1,3],specifi:[0,3],splunkclient:0,spunk:3,src:[1,4],ssh:[3,4],stack:4,stage:0,starter:4,stash:4,statu:0,step:4,stick:3,sticki:4,store:[0,2,4],str:[0,3],string:[0,3],substitut:4,success:[0,4],support:[1,2,3,4],sure:[1,4],sync:0,tab:4,tag:[0,2,4],take:[2,3],team:0,technolog:2,tell:4,templat:4,termin:4,test:[0,1],than:[2,4],thei:[1,4],them:4,thi:[0,2,3,4],thing:4,those:0,tier:4,time:[0,2,4],todai:[1,2],token:[0,3],token_id:0,token_nam:3,token_secret:0,told:4,top:4,touch:4,trial:4,trigger:[0,4],two:[2,4],txt:[1,4],type:[0,3,4],uat:4,under:[3,4],union:3,unless:1,updat:[0,1,4],update_app_config:0,update_repo_deployment_vari:0,update_repo_vari:0,update_secret:0,update_secret_descript:0,update_team_pipeline_vari:0,updatesecretexcept:0,uri:0,url:0,us3:[0,3],use:[2,3,4],used:[1,3],user:[0,2,3,4],userid:0,usernam:[0,3,4],userpoolconfig:0,userpoolid:0,using:[3,4],uuid:0,valid:0,validate_spec:3,validationexcept:0,valu:[0,3,4],var_uuid:0,variabl:[0,2,3,4],veri:4,verifi:[0,3],version:0,version_stag:0,versionid:0,versionidstostag:0,versionstag:0,via:3,virtualenv:4,wafwebaclarn:0,wai:4,want:4,web:4,week:2,well:1,what:[1,4],whatev:1,when:3,where:1,which:[0,1,2,3,4],why:[1,4],without:[0,2,4],word:3,work:[0,1],worri:1,would:4,wrong:1,www:3,xrayen:0,yaml:[1,3,4],yet:3,you:[1,2],your:[1,2,3,4]},titles:["Clients","Developing Keydra","Keydra - Secrets Management for Humans!","Providers","Getting Started"],titleterms:{AWS:[0,3,4],appsync:[0,3],bitbucket:[0,3],bootstrap:4,client:[0,1],cloudflar:[0,3],configur:4,content:[0,3],contribut:1,deploi:4,deploy:4,develop:1,distribut:1,get:4,guidelin:1,human:2,iam:[0,3],initi:4,keydra:[1,2,4],manag:[0,2,3],need:4,provid:[1,3],quali:[0,3],repositori:4,rotat:1,run:4,salesforc:[0,3],secret:[0,2,3],setup:4,splunk:[0,3],start:4,test:4,you:4}})