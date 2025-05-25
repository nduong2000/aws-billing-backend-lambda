const db = require('../config/db');
const axios = require('axios');
require('dotenv').config(); // Ensure env vars are loaded

// Ollama configuration is now expected from the request body
// const OLLAMA_API_URL = process.env.OLLAMA_API_URL || 'http://localhost:11434'; // Removed
// const OLLAMA_MODEL = 'mistral:7b'; // Removed

// Helper to format data for the LLM prompt
const formatClaimDataForLLM = (claim, items, patient, provider) => {
  let promptData = `Claim ID: ${claim.claim_id}\n`;
  promptData += `Claim Date: ${new Date(claim.claim_date).toLocaleDateString()}\n`;
  promptData += `Claim Status: ${claim.status}\n`;
  // Convert currency strings to numbers before formatting
  promptData += `Total Charge: $${Number(claim.total_charge).toFixed(2)}\n`;
  promptData += `Insurance Paid: $${Number(claim.insurance_paid).toFixed(2)}\n`;
  promptData += `Patient Paid: $${Number(claim.patient_paid).toFixed(2)}\n\n`;

  promptData += `Patient: ${patient.first_name} ${patient.last_name} (ID: ${patient.patient_id}, DOB: ${new Date(patient.date_of_birth).toLocaleDateString()})\n`;
  promptData += `Insurance: ${patient.insurance_provider || 'N/A'} (Policy: ${patient.insurance_policy_number || 'N/A'})\n\n`;

  promptData += `Provider: ${provider.provider_name} (ID: ${provider.provider_id}, NPI: ${provider.npi_number}, Specialty: ${provider.specialty || 'N/A'})\n\n`;

  promptData += `Services Billed:\n`;
  items.forEach(item => {
    // Convert item charge amount too
    promptData += `- CPT Code: ${item.cpt_code}, Description: ${item.description}, Charge: $${Number(item.charge_amount).toFixed(2)}\n`;
  });

  return promptData;
}

// @desc    Analyze a claim for anomalies using Ollama
// @route   POST /api/claims/:id/audit
// @access  Private // TODO: Add auth
const auditClaimWithOllama = async (req, res, next) => {
  // --- START: Added Log ---
  console.log(`[Audit Controller] ENTERED auditClaimWithOllama function for Claim ID: ${req.params.id}`);
  // --- END: Added Log ---

  const { id } = req.params;
  const { targetOllamaUrl, targetOllamaModel } = req.body;

  // --- Validation --- 
  if (!targetOllamaUrl || !targetOllamaModel) {
    return res.status(400).json({ message: 'Missing targetOllamaUrl or targetOllamaModel in request body.' });
  }
  // Basic URL format check (can be improved)
  if (!targetOllamaUrl.startsWith('http://') && !targetOllamaUrl.startsWith('https://')) {
      return res.status(400).json({ message: 'Invalid targetOllamaUrl format.' });
  }
  console.log(`[Audit Controller] Received request to audit claim ID: ${id}`);
  console.log(`[Audit Controller] Target Ollama URL: ${targetOllamaUrl}`);
  console.log(`[Audit Controller] Target Ollama Model: ${targetOllamaModel}`);
  // --- End Validation ---

  try {
    // --- START: Added Log ---
    console.log(`[Audit Controller] Attempting to fetch data for claim ${id}...`);
    // --- END: Added Log ---

    // 1. Fetch comprehensive claim data
    const claimQuery = db.query('SELECT * FROM claims WHERE claim_id = $1', [id]);
    const itemsQuery = db.query('SELECT ci.*, s.cpt_code, s.description FROM claim_items ci JOIN services s ON ci.service_id = s.service_id WHERE ci.claim_id = $1', [id]);
    const claimResult = await claimQuery;
    if (claimResult.rowCount === 0) {
      return res.status(404).json({ message: 'Claim not found' });
    }
    const claim = claimResult.rows[0];
    const [itemsResult, patientResult, providerResult] = await Promise.all([
        itemsQuery,
        db.query('SELECT * FROM patients WHERE patient_id = $1', [claim.patient_id]),
        db.query('SELECT * FROM providers WHERE provider_id = $1', [claim.provider_id])
    ]);
    if (patientResult.rowCount === 0 || providerResult.rowCount === 0) {
        return res.status(404).json({ message: 'Associated patient or provider not found' });
    }
    const items = itemsResult.rows;
    const patient = patientResult.rows[0];
    const provider = providerResult.rows[0];

    // --- START: Added Log ---
    console.log(`[Audit Controller] Successfully fetched data for claim ${id}.`);
    // --- END: Added Log ---

    // 2. Format data and create the prompt
    const formattedData = formatClaimDataForLLM(claim, items, patient, provider);
    const prompt = `You are a medical billing auditor. Analyze the following medical claim data and identify potential anomalies, errors, inconsistencies, or areas needing review (like potential upcoding/downcoding, mismatches between services and provider specialty, unusual charges, duplicate services, etc.). Explain your reasoning clearly for each identified point. If no issues are found, state that clearly.\n\nClaim Data:\n${formattedData}`;

    console.log(`Sending prompt to Ollama (${targetOllamaModel}) at ${targetOllamaUrl} for claim: ${id}`);

    // --- START: Added Log ---
    console.log(`[Audit Controller] Making axios POST request to Ollama...`);
    // --- END: Added Log ---

    // 3. Call Ollama API (using parameters from request)
    const ollamaResponse = await axios.post(`${targetOllamaUrl}/api/generate`, {
        model: targetOllamaModel, // Use model from request
        prompt: prompt,
        stream: false
    }, {
        headers: { 'Content-Type': 'application/json' }
    });

    // --- START: Added Log ---
    console.log(`[Audit Controller] Received response from Ollama. Status: ${ollamaResponse.status}`);
    // --- END: Added Log ---

    console.log(`Received response from Ollama for claim: ${id}`);

    // 4. Send back the LLM's analysis
    res.status(200).json({
        claim_id: id,
        analysis: ollamaResponse.data?.response?.trim() || 'No response text from Ollama.'
    });

  } catch (err) {
    // --- START: Added Log ---
    console.error(`[Audit Controller] CAUGHT ERROR in auditClaimWithOllama for claim ${id}.`);
    // --- END: Added Log ---
    console.error(`Error auditing claim ${id} with Ollama (${targetOllamaModel} at ${targetOllamaUrl}):`, err.response?.data || err.message);
    if (err.code === 'ECONNREFUSED' || err.message.includes('ECONNREFUSED')) {
        return res.status(503).json({ message: `Could not connect to Ollama API at ${targetOllamaUrl}. Is it running and accessible?` });
    } else if (err.response?.status === 404 && err.config?.url?.includes('/api/generate')) {
        // Handle case where the model might not exist on the target Ollama instance
        return res.status(400).json({ message: `Model '${targetOllamaModel}' not found on Ollama instance at ${targetOllamaUrl}. Ensure the model is pulled.`});
    }
    next(err);
  }
};

module.exports = {
    auditClaimWithOllama
}; 