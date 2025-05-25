import React, { useState } from 'react';
import { ArrowRight, ArrowDown, Database, Server, Globe, Users, FileText, CreditCard, FileCheck, BarChart4, Cloud } from 'lucide-react';

const SystemArchitectureDiagrams = () => {
  const [activeTab, setActiveTab] = useState(0);

  const tabs = [
    "High-Level System Architecture",
    "AWS Deployment Architecture",
    "Application Component Architecture",
    "Data Flow Diagram",
    "Database Schema Diagram",
    "Audit Process Flow",
    "Deployment Process Flow"
  ];
  
  // Common styles
  const componentStyle = "flex flex-col items-center justify-center p-4 bg-white border border-gray-300 shadow-md rounded-lg";
  const arrowStyle = "text-gray-600 mx-2";
  const labelStyle = "text-sm font-semibold mt-2";
  const containerStyle = "flex flex-col items-center justify-center bg-gray-50 p-8 rounded-xl border border-gray-200";
  const descriptionStyle = "text-sm text-gray-600 italic mt-2 mb-6 max-w-3xl text-center";
  
  // Component for rendering the High-Level System Architecture
  const HighLevelArchitecture = () => (
    <div className={containerStyle}>
      <p className={descriptionStyle}>
        Overview of the main components in the Medical Billing System and their interactions
      </p>
      
      <div className="flex flex-col items-center gap-6">
        <div className="flex items-center">
          <div className={componentStyle}>
            <Globe size={36} className="text-blue-500" />
            <span className={labelStyle}>Web Browser</span>
          </div>
          
          <div className="flex items-center mx-2">
            <ArrowRight className={arrowStyle} />
            <ArrowLeft className={arrowStyle} />
          </div>
          
          <div className={componentStyle}>
            <FileText size={36} className="text-green-500" />
            <span className={labelStyle}>Frontend App</span>
          </div>
          
          <div className="flex items-center mx-2">
            <ArrowRight className={arrowStyle} />
            <ArrowLeft className={arrowStyle} />
          </div>
          
          <div className={componentStyle}>
            <Server size={36} className="text-purple-500" />
            <span className={labelStyle}>API Backend</span>
          </div>
        </div>
        
        <ArrowDown className="text-gray-600 my-2" />
        
        <div className="flex items-center">
          <div className={componentStyle}>
            <Cloud size={36} className="text-orange-500" />
            <span className={labelStyle}>AWS Bedrock (AI/ML)</span>
          </div>
          
          <div className="flex items-center mx-2">
            <ArrowRight className={arrowStyle} />
            <ArrowLeft className={arrowStyle} />
          </div>
          
          <div className={componentStyle}>
            <Database size={36} className="text-blue-600" />
            <span className={labelStyle}>PostgreSQL DB</span>
          </div>
        </div>
      </div>
    </div>
  );
  
  // Component for rendering the AWS Deployment Architecture
  const AWSDeploymentArchitecture = () => (
    <div className={containerStyle}>
      <p className={descriptionStyle}>
        Deployment architecture showing how the system is deployed on AWS infrastructure
      </p>
      
      <div className="border-2 border-blue-300 rounded-xl p-6 bg-blue-50">
        <div className="text-center font-bold text-blue-700 mb-6">AWS Cloud</div>
        
        <div className="flex flex-col items-center gap-6">
          <div className="flex items-center">
            <div className={componentStyle}>
              <Globe size={30} className="text-blue-500" />
              <span className={labelStyle}>Route 53 (DNS)</span>
            </div>
            
            <ArrowRight className={arrowStyle} />
            
            <div className={componentStyle}>
              <Server size={30} className="text-green-500" />
              <span className={labelStyle}>Elastic Load Balancer</span>
            </div>
          </div>
          
          <ArrowDown className="text-gray-600 my-1" />
          
          <div className="flex items-center">
            <div className={componentStyle + " mr-6"}>
              <FileText size={30} className="text-amber-500" />
              <span className={labelStyle}>S3 Bucket (Static Files)</span>
            </div>
            
            <div className={componentStyle}>
              <Server size={30} className="text-green-600" />
              <span className={labelStyle}>Elastic Beanstalk</span>
            </div>
          </div>
          
          <ArrowDown className="text-gray-600 my-1" />
          
          <div className="flex items-center">
            <div className={componentStyle}>
              <Cloud size={30} className="text-orange-500" />
              <span className={labelStyle}>AWS Bedrock (AI Audit)</span>
            </div>
            
            <div className="flex items-center mx-2">
              <ArrowRight className={arrowStyle} />
              <ArrowLeft className={arrowStyle} />
            </div>
            
            <div className={componentStyle}>
              <Database size={30} className="text-blue-600" />
              <span className={labelStyle}>RDS (PostgreSQL)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
  
  // Component for rendering the Application Component Architecture
  const ApplicationComponentArchitecture = () => (
    <div className={containerStyle}>
      <p className={descriptionStyle}>
        Logical architecture showing the main modules of the FastAPI application
      </p>
      
      <div className="border-2 border-purple-300 rounded-xl p-6 bg-purple-50">
        <div className="text-center font-bold text-purple-700 mb-6">FastAPI Application</div>
        
        <div className="flex flex-col items-center gap-6">
          <div className="flex items-center gap-4">
            <div className={componentStyle}>
              <Users size={28} className="text-blue-500" />
              <span className={labelStyle}>Patient Module</span>
            </div>
            
            <div className={componentStyle}>
              <Users size={28} className="text-green-500" />
              <span className={labelStyle}>Provider Module</span>
            </div>
            
            <div className={componentStyle}>
              <FileText size={28} className="text-amber-500" />
              <span className={labelStyle}>Service Module</span>
            </div>
          </div>
          
          <div className="flex justify-center w-full">
            <ArrowDown className="text-gray-600 mx-4" />
            <ArrowDown className="text-gray-600 mx-4" />
            <ArrowDown className="text-gray-600 mx-4" />
          </div>
          
          <div className="flex items-center gap-4">
            <div className={componentStyle}>
              <FileText size={28} className="text-purple-500" />
              <span className={labelStyle}>Appointment Module</span>
            </div>
            
            <div className={componentStyle}>
              <FileCheck size={28} className="text-red-500" />
              <span className={labelStyle}>Claim Module</span>
            </div>
            
            <div className={componentStyle}>
              <CreditCard size={28} className="text-blue-600" />
              <span className={labelStyle}>Payment Module</span>
            </div>
          </div>
          
          <div className="flex justify-center w-full">
            <div className="border-l-2 border-gray-400 h-8"></div>
          </div>
          
          <div className={componentStyle + " border-orange-200 bg-orange-50"}>
            <BarChart4 size={30} className="text-orange-500" />
            <span className={labelStyle}>Audit Module (Bedrock AI)</span>
          </div>
        </div>
      </div>
    </div>
  );
  
  // Component for rendering the Data Flow Diagram
  const DataFlowDiagram = () => (
    <div className={containerStyle}>
      <p className={descriptionStyle}>
        Diagram showing how data flows through the different components of the system
      </p>
      
      <div className="flex flex-col items-center gap-6">
        <div className="flex items-center gap-4">
          <div className={componentStyle}>
            <Users size={28} className="text-blue-500" />
            <span className={labelStyle}>Patient Data</span>
          </div>
          
          <ArrowRight className={arrowStyle} />
          
          <div className={componentStyle}>
            <Users size={28} className="text-green-500" />
            <span className={labelStyle}>Provider Data</span>
          </div>
          
          <ArrowRight className={arrowStyle} />
          
          <div className={componentStyle}>
            <FileText size={28} className="text-amber-500" />
            <span className={labelStyle}>Service Data</span>
          </div>
          
          <ArrowRight className={arrowStyle} />
          
          <div className={componentStyle}>
            <FileText size={28} className="text-purple-500" />
            <span className={labelStyle}>Appointment Data</span>
          </div>
        </div>
        
        <div className="flex w-full items-center justify-between px-12">
          <div className="border-l-2 border-gray-400 h-12"></div>
          <div className="border-l-2 border-gray-400 h-12"></div>
        </div>
        
        <div className="flex items-center gap-4">
          <div className={componentStyle}>
            <CreditCard size={28} className="text-blue-600" />
            <span className={labelStyle}>Payment Processing</span>
          </div>
          
          <ArrowLeft className={arrowStyle} />
          
          <div className={componentStyle}>
            <FileCheck size={28} className="text-red-500" />
            <span className={labelStyle}>Claim Processing</span>
          </div>
        </div>
        
        <div className="flex w-full items-center justify-center">
          <div className="border-l-2 border-gray-400 h-12"></div>
        </div>
        
        <div className={componentStyle + " border-orange-200 bg-orange-50"}>
          <BarChart4 size={30} className="text-orange-500" />
          <span className={labelStyle}>Audit System</span>
        </div>
      </div>
    </div>
  );
  
  // Component for rendering the Database Schema Diagram
  const DatabaseSchemaDiagram = () => (
    <div className={containerStyle}>
      <p className={descriptionStyle}>
        Simplified database schema showing the main tables and their relationships
      </p>
      
      <div className="flex flex-col items-center gap-10 overflow-auto max-w-full">
        <div className="flex items-start gap-10">
          <div className="border border-blue-300 rounded-lg p-4 bg-blue-50">
            <div className="font-bold text-blue-700 mb-2 border-b pb-1">patients</div>
            <div className="text-sm mb-1">patient_id (PK)</div>
            <div className="text-sm mb-1">first_name</div>
            <div className="text-sm mb-1">last_name</div>
            <div className="text-sm mb-1">dob</div>
            <div className="text-sm mb-1">address</div>
            <div className="text-sm">phone</div>
          </div>
          
          <div className="border border-green-300 rounded-lg p-4 bg-green-50">
            <div className="font-bold text-green-700 mb-2 border-b pb-1">providers</div>
            <div className="text-sm mb-1">provider_id (PK)</div>
            <div className="text-sm mb-1">provider_name</div>
            <div className="text-sm mb-1">specialty</div>
            <div className="text-sm mb-1">npi_number</div>
            <div className="text-sm mb-1">tax_id</div>
            <div className="text-sm">address</div>
          </div>
          
          <div className="border border-amber-300 rounded-lg p-4 bg-amber-50">
            <div className="font-bold text-amber-700 mb-2 border-b pb-1">services</div>
            <div className="text-sm mb-1">service_id (PK)</div>
            <div className="text-sm mb-1">cpt_code</div>
            <div className="text-sm mb-1">description</div>
            <div className="text-sm">base_price</div>
          </div>
        </div>
        
        <div className="flex items-start gap-10">
          <div className="border border-purple-300 rounded-lg p-4 bg-purple-50">
            <div className="font-bold text-purple-700 mb-2 border-b pb-1">appointments</div>
            <div className="text-sm mb-1">appointment_id (PK)</div>
            <div className="text-sm mb-1">patient_id (FK)</div>
            <div className="text-sm mb-1">provider_id (FK)</div>
            <div className="text-sm mb-1">appointment_date</div>
            <div className="text-sm mb-1">appointment_type</div>
            <div className="text-sm">notes</div>
          </div>
          
          <div className="border border-red-300 rounded-lg p-4 bg-red-50">
            <div className="font-bold text-red-700 mb-2 border-b pb-1">claims</div>
            <div className="text-sm mb-1">claim_id (PK)</div>
            <div className="text-sm mb-1">patient_id (FK)</div>
            <div className="text-sm mb-1">provider_id (FK)</div>
            <div className="text-sm mb-1">claim_date</div>
            <div className="text-sm mb-1">total_amount</div>
            <div className="text-sm mb-1">status</div>
            <div className="text-sm">fraud_score</div>
          </div>
        </div>
        
        <div className="flex items-start gap-10">
          <div className="border border-indigo-300 rounded-lg p-4 bg-indigo-50">
            <div className="font-bold text-indigo-700 mb-2 border-b pb-1">claim_items</div>
            <div className="text-sm mb-1">item_id (PK)</div>
            <div className="text-sm mb-1">claim_id (FK)</div>
            <div className="text-sm mb-1">service_id (FK)</div>
            <div className="text-sm mb-1">quantity</div>
            <div className="text-sm">charge_amount</div>
          </div>
          
          <div className="border border-blue-300 rounded-lg p-4 bg-blue-50">
            <div className="font-bold text-blue-700 mb-2 border-b pb-1">payments</div>
            <div className="text-sm mb-1">payment_id (PK)</div>
            <div className="text-sm mb-1">claim_id (FK)</div>
            <div className="text-sm mb-1">payment_date</div>
            <div className="text-sm mb-1">payment_amount</div>
            <div className="text-sm mb-1">payment_method</div>
            <div className="text-sm">status</div>
          </div>
        </div>
      </div>
    </div>
  );
  
  // Component for rendering the Audit Process Flow
  const AuditProcessFlow = () => (
    <div className={containerStyle}>
      <p className={descriptionStyle}>
        Flow diagram showing the audit process using AWS Bedrock for claim analysis
      </p>
      
      <div className="flex flex-wrap justify-center gap-4">
        <div className="flex items-center">
          <div className={componentStyle}>
            <FileCheck size={28} className="text-blue-500" />
            <span className={labelStyle}>Claim Submission</span>
          </div>
          
          <ArrowRight className={arrowStyle} />
          
          <div className={componentStyle}>
            <FileText size={28} className="text-purple-500" />
            <span className={labelStyle}>Format Claim Data for LLM</span>
          </div>
          
          <ArrowRight className={arrowStyle} />
          
          <div className={componentStyle + " border-orange-200 bg-orange-50"}>
            <Cloud size={28} className="text-orange-500" />
            <span className={labelStyle}>AWS Bedrock AI Analysis</span>
          </div>
          
          <ArrowRight className={arrowStyle} />
          
          <div className={componentStyle}>
            <BarChart4 size={28} className="text-red-500" />
            <span className={labelStyle}>Calculate Fraud Score</span>
          </div>
        </div>
        
        <div className="flex w-full justify-end pr-16">
          <ArrowDown className="text-gray-600" />
        </div>
        
        <div className="flex items-center">
          <div className={componentStyle}>
            <Database size={28} className="text-blue-600" />
            <span className={labelStyle}>Store Audit Results</span>
          </div>
          
          <ArrowLeft className={arrowStyle} />
          
          <div className={componentStyle}>
            <FileCheck size={28} className="text-green-500" />
            <span className={labelStyle}>Update Claim Status</span>
          </div>
          
          <ArrowLeft className={arrowStyle} />
          
          <div className={componentStyle}>
            <FileText size={28} className="text-amber-500" />
            <span className={labelStyle}>Generate Audit Report</span>
          </div>
          
          <ArrowLeft className={arrowStyle} />
          
          <div className={componentStyle}>
            <BarChart4 size={28} className="text-purple-600" />
            <span className={labelStyle}>ML Fraud Detection</span>
          </div>
        </div>
      </div>
    </div>
  );
  
  // Component for rendering the Deployment Process Flow
  const DeploymentProcessFlow = () => (
    <div className={containerStyle}>
      <p className={descriptionStyle}>
        Flow diagram showing the deployment process for the application on AWS infrastructure
      </p>
      
      <div className="flex flex-wrap justify-center gap-4">
        <div className="flex items-center">
          <div className={componentStyle}>
            <FileText size={28} className="text-blue-500" />
            <span className={labelStyle}>Local Dev Environment</span>
          </div>
          
          <ArrowRight className={arrowStyle} />
          
          <div className={componentStyle}>
            <FileCheck size={28} className="text-purple-500" />
            <span className={labelStyle}>Git Commit Changes</span>
          </div>
          
          <ArrowRight className={arrowStyle} />
          
          <div className={componentStyle}>
            <Cloud size={28} className="text-green-500" />
            <span className={labelStyle}>Create EB App Version</span>
          </div>
          
          <ArrowRight className={arrowStyle} />
          
          <div className={componentStyle}>
            <Database size={28} className="text-amber-500" />
            <span className={labelStyle}>Upload to S3 Bucket</span>
          </div>
        </div>
        
        <div className="flex w-full justify-end pr-16">
          <ArrowDown className="text-gray-600" />
        </div>
        
        <div className="flex items-center">
          <div className={componentStyle}>
            <Globe size={28} className="text-blue-600" />
            <span className={labelStyle}>Domain Setup</span>
          </div>
          
          <ArrowLeft className={arrowStyle} />
          
          <div className={componentStyle}>
            <Cloud size={28} className="text-green-500" />
            <span className={labelStyle}>Configure HTTPS & CORS</span>
          </div>
          
          <ArrowLeft className={arrowStyle} />
          
          <div className={componentStyle}>
            <Server size={28} className="text-purple-600" />
            <span className={labelStyle}>Deploy to Elastic Beanstalk</span>
          </div>
          
          <ArrowLeft className={arrowStyle} />
          
          <div className={componentStyle}>
            <Cloud size={28} className="text-red-500" />
            <span className={labelStyle}>EB Environment Setup</span>
          </div>
        </div>
      </div>
    </div>
  );

  const ArrowLeft = ({ className }) => (
    <div className={className}>
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M19 12H5"/>
        <path d="M12 19l-7-7 7-7"/>
      </svg>
    </div>
  );

  return (
    <div className="bg-white p-6 rounded-xl shadow-lg">
      <h1 className="text-2xl font-bold text-center mb-6">Medical Billing System Architecture</h1>
      
      <div className="flex flex-wrap gap-2 justify-center mb-8">
        {tabs.map((tab, index) => (
          <button
            key={index}
            onClick={() => setActiveTab(index)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors
                      ${activeTab === index 
                        ? 'bg-blue-600 text-white' 
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
          >
            {tab}
          </button>
        ))}
      </div>
      
      <div className="mt-4">
        {activeTab === 0 && <HighLevelArchitecture />}
        {activeTab === 1 && <AWSDeploymentArchitecture />}
        {activeTab === 2 && <ApplicationComponentArchitecture />}
        {activeTab === 3 && <DataFlowDiagram />}
        {activeTab === 4 && <DatabaseSchemaDiagram />}
        {activeTab === 5 && <AuditProcessFlow />}
        {activeTab === 6 && <DeploymentProcessFlow />}
      </div>
    </div>
  );
};

export default SystemArchitectureDiagrams;